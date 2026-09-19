"""Kokoro-82M TTS backend (Apache-2.0, MLX on Apple Silicon)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from tts.base import TTSBackend
from tts.breaks import (
    AURITUS_BREAK_MARKER,
    AURITUS_PAUSE_MARKER,
    DEFAULT_PAUSE_SILENCE_SECONDS,
    parse_voiced_segments,
    split_on_breaks,
    split_on_pauses,
)

__all__ = [
    "AURITUS_BREAK_MARKER",
    "AURITUS_PAUSE_MARKER",
    "KokoroBackend",
    "parse_voiced_segments",
    "resolve_kokoro_voice",
    "split_on_breaks",
    "split_on_pauses",
]

KOKORO_DEFAULT_VOICE = "af_heart"
BREAK_SILENCE_SECONDS = 0.75
PAUSE_SILENCE_SECONDS = DEFAULT_PAUSE_SILENCE_SECONDS


def resolve_kokoro_voice(meta: dict[str, Any]) -> str:
    """Return the Kokoro voice id, mapping missing or legacy values to the default.

    :param meta: Job metadata containing an optional ``voice_id``.
    :returns: Kokoro voice id suitable for synthesis.
    """
    raw = meta.get("voice_id")
    if raw is None:
        return KOKORO_DEFAULT_VOICE
    if isinstance(raw, str) and (not raw.strip() or raw == "default"):
        return KOKORO_DEFAULT_VOICE
    return str(raw)


class KokoroBackend(TTSBackend):
    """Kokoro TTS backend using mlx-audio on Apple Silicon.

    Loads mlx-community/Kokoro-82M-bf16 at runtime via mlx-audio.
    Falls back to PyTorch kokoro on non-Apple platforms.
    """

    name = "kokoro"
    _model = None
    _is_mlx = None

    @classmethod
    def _detect_mlx(cls) -> bool:
        """Detect whether MLX is available on this platform."""
        import platform

        if platform.system() != "Darwin":
            return False
        machine = platform.machine().lower()
        return machine.startswith(("arm", "aarch"))

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate speech audio using Kokoro-82M.

        On Apple Silicon: uses mlx-audio (fast, native MLX).
        On other platforms: falls back to PyTorch kokoro (slow).

        :param text: TTS input text.
        :param meta: Job metadata (voice_id, name, byline).
        :returns: WAV audio bytes at 24000 Hz mono 16-bit.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if KokoroBackend._is_mlx is None:
            KokoroBackend._is_mlx = KokoroBackend._detect_mlx()

        if KokoroBackend._is_mlx:
            return self._generate_mlx(text, meta)
        return self._generate_torch(text, meta)

    def _generate_mlx(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via mlx-audio (Apple Silicon).

        Two layers of splitting happen here, for different reasons:

        1. Block splitting (split_on_breaks): the embed generator marks
           paragraph/heading/etc. boundaries with AURITUS_BREAK_MARKER. Each
           block is synthesized separately so a real silence gap can be
           inserted between them -- otherwise a heading reads flush against
           the paragraph that follows it.
        2. Segment splitting (model.generate() itself): within a single
           block, Kokoro's own pipeline further splits long text into
           speakable chunks due to a model sequence-length limit (nothing to
           do with paragraphs). model.generate() is a generator yielding one
           GenerationResult per segment; taking only the first discards
           everything past it, silently truncating any block long enough to
           need more than one.

        Every block's every segment gets concatenated, with silence between
        blocks only (not between a block's own internal segments, which are
        mid-thought splits, not real pauses).
        """
        import numpy as np
        from mlx_audio.tts.utils import load_model

        if KokoroBackend._model is None:
            KokoroBackend._model = load_model(
                "mlx-community/Kokoro-82M-bf16",
                lazy=False,
            )
        default_voice = resolve_kokoro_voice(meta)
        sample_rate = 24000
        block_audios: list[np.ndarray] = []
        pause_gap = np.zeros(int(sample_rate * PAUSE_SILENCE_SECONDS), dtype=np.float32)
        for block_text, block_voice in parse_voiced_segments(text, default_voice):
            pause_segments = split_on_pauses(block_text)
            block_parts: list[np.ndarray] = []
            for p_idx, pause_text in enumerate(pause_segments):
                if p_idx > 0:
                    block_parts.append(pause_gap)
                gen = KokoroBackend._model.generate(pause_text, voice=block_voice)
                segments = [np.array(result.audio) for result in gen]
                if segments:
                    block_parts.append(
                        np.concatenate(segments) if len(segments) > 1 else segments[0]
                    )
            if block_parts:
                block_audios.append(
                    np.concatenate(block_parts)
                    if len(block_parts) > 1
                    else block_parts[0]
                )
        if not block_audios:
            raise ValueError("Kokoro generated no audio segments")
        audio_np = _join_with_silence(block_audios, sample_rate)
        return _to_wav(audio_np, sample_rate=sample_rate)

    def _generate_torch(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via PyTorch kokoro (fallback for non-Apple, e.g. AWS Batch).

        Same two-layer split as the MLX path (see _generate_mlx): blocks on
        AURITUS_BREAK_MARKER for real pauses, segments from KPipeline's own
        generator within each block for Kokoro's internal length limit.

        KPipeline's own device default was previously trusted implicitly;
        explicitly resolves and passes cuda/cpu here (mirroring higgs.py,
        chatterbox.py, qwen.py) so a g4dn.xlarge Batch run is verified, not
        assumed, to actually use the GPU it's billed for.
        """
        import torch
        from kokoro import KPipeline

        if KokoroBackend._model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[kokoro] resolved device={device}", flush=True)
            KokoroBackend._model = KPipeline(lang_code="a", device=device)
        default_voice = resolve_kokoro_voice(meta)
        sample_rate = 24000
        block_silence = [0.0] * int(sample_rate * BREAK_SILENCE_SECONDS)
        pause_silence = [0.0] * int(sample_rate * PAUSE_SILENCE_SECONDS)
        audio_list: list[float] = []
        for block_text, block_voice in parse_voiced_segments(text, default_voice):
            if audio_list:
                audio_list.extend(block_silence)
            pause_segments = split_on_pauses(block_text)
            for p_idx, pause_text in enumerate(pause_segments):
                if p_idx > 0:
                    audio_list.extend(pause_silence)
                results = list(KokoroBackend._model(pause_text, voice=block_voice))
                for result in results:
                    audio_tensor = result.audio
                    audio_list.extend(
                        audio_tensor.tolist()
                        if hasattr(audio_tensor, "tolist")
                        else list(audio_tensor)
                    )
        if not audio_list:
            raise ValueError("Kokoro generated no audio segments")
        return _to_wav(audio_list, sample_rate=sample_rate)


def _join_with_silence(blocks: list, sample_rate: int) -> Any:
    """Concatenate per-block audio arrays with a silence gap between them.

    :param blocks: One numpy array per AURITUS_BREAK_MARKER-delimited block,
        in order. Never empty (callers raise before this is called otherwise).
    :param sample_rate: Sample rate the blocks were generated at.
    :returns: A single concatenated array; the type matches ``blocks``'
        element type (numpy is an optional dependency of this module, so it
        isn't imported at module scope only to name it here).
    """
    import numpy as np

    if len(blocks) == 1:
        return blocks[0]
    silence = np.zeros(int(sample_rate * BREAK_SILENCE_SECONDS), dtype=blocks[0].dtype)
    pieces = []
    for i, block in enumerate(blocks):
        if i > 0:
            pieces.append(silence)
        pieces.append(block)
    return np.concatenate(pieces)


def _to_wav(samples: list, sample_rate: int = 24000) -> bytes:
    """Convert normalized audio samples to mono 16-bit WAV bytes."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = struct.pack(
            "<" + "h" * len(samples),
            *[
                max(-32768, min(32767, int(float(sample) * 32767)))
                for sample in samples
            ],
        )
        handle.writeframes(frames)
    return buffer.getvalue()
