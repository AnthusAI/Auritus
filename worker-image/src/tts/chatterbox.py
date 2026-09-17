"""Chatterbox-TTS (Resemble AI) backend for AWS Batch and Linux GPU workers.

Weights are fetched at runtime per docs/TTS_LICENSES.md.
"""

from __future__ import annotations

import io
import math
import struct
import wave
from typing import Any

from tts.base import TTSBackend
from tts.breaks import AURITUS_BREAK_MARKER, split_on_breaks

__all__ = [
    "AURITUS_BREAK_MARKER",
    "split_on_breaks",
    "ChatterboxBackend",
    "resolve_chatterbox_voice",
]

CHATTERBOX_DEFAULT_VOICE = "default"
CHATTERBOX_TORCH_MODEL = "ResembleAI/chatterbox"
CHATTERBOX_MLX_MODEL = "mlx-community/Chatterbox-TTS-fp16"

# How long a real silence gap is between AURITUS_BREAK_MARKER-delimited
# blocks for this specific backend/voice. The marker itself and how it's
# split live in tts.breaks, shared by every backend -- only the gap length
# is a per-backend tuning choice.
BREAK_SILENCE_SECONDS = 0.4


def resolve_chatterbox_voice(meta: dict[str, Any]) -> str:
    """Return a Chatterbox voice or reference style name for synthesis.

    :param meta: Job metadata containing an optional ``voice_id``.
    :returns: Voice identifier string.
    """
    raw = meta.get("voice_id")
    if raw is None:
        return CHATTERBOX_DEFAULT_VOICE
    if isinstance(raw, str) and not raw.strip():
        return CHATTERBOX_DEFAULT_VOICE
    return str(raw)


class ChatterboxBackend(TTSBackend):
    """Chatterbox-TTS backend using Resemble AI Chatterbox.

    On Apple Silicon: loads mlx-community/Chatterbox-TTS-fp16 via mlx-audio.
    On Linux / AWS Batch GPU: loads ResembleAI/chatterbox via PyTorch on CUDA.
    """

    name = "chatterbox"
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
        """Generate speech audio using Chatterbox-TTS.

        :param text: TTS input text.
        :param meta: Job metadata (voice_id, name, byline).
        :returns: WAV audio bytes at 24000 Hz mono 16-bit.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if ChatterboxBackend._is_mlx is None:
            ChatterboxBackend._is_mlx = ChatterboxBackend._detect_mlx()

        if ChatterboxBackend._is_mlx:
            return self._generate_mlx(text, meta)
        return self._generate_torch(text, meta)

    def _generate_mlx(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via mlx-audio on Apple Silicon."""
        import numpy as np
        from mlx_audio.tts.utils import load_model

        if ChatterboxBackend._model is None:
            ChatterboxBackend._model = load_model(
                CHATTERBOX_MLX_MODEL,
                lazy=False,
            )
        sample_rate = int(
            getattr(
                ChatterboxBackend._model,
                "sample_rate",
                getattr(ChatterboxBackend._model, "sr", 24000),
            )
        )
        blocks = split_on_breaks(text)
        all_chunks: list[np.ndarray] = []
        silence = np.zeros(int(sample_rate * BREAK_SILENCE_SECONDS), dtype=np.float32)

        for i, block in enumerate(blocks):
            if i > 0:
                all_chunks.append(silence)
            gen = ChatterboxBackend._model.generate(block)
            block_chunks = [np.array(result.audio) for result in gen]
            if block_chunks:
                all_chunks.extend(block_chunks)

        if not all_chunks:
            raise ValueError("Chatterbox-TTS generated no audio segments")
        audio_np = np.concatenate(all_chunks) if len(all_chunks) > 1 else all_chunks[0]
        return _to_wav(audio_np, sample_rate=sample_rate)

    def _generate_torch(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via PyTorch / CUDA, or a stub tone when the package isn't installed.

        Only ImportError falls back to the stub -- a missing optional
        dependency (e.g. running a quick smoke test without the heavy
        torch/chatterbox install) is a legitimate reason to stub. A model
        that loads and then fails mid-generation (OOM, a CUDA error, an
        actual bug) must raise: swallowing every exception here previously
        meant any real failure silently produced a normal-looking 'done'
        job with a fake 440Hz tone as its audio -- indistinguishable from
        success to a reader, and to the job API. Let real errors surface so
        the job is correctly marked failed with the actual error_message.
        """
        try:
            import numpy as np
            import torch
            from chatterbox.tts import ChatterboxTTS
        except ImportError:
            return self._generate_fallback(text, meta)

        if ChatterboxBackend._model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"[chatterbox] resolved device={device}", flush=True)
            ChatterboxBackend._model = ChatterboxTTS.from_pretrained(
                device=device,
            )
        blocks = split_on_breaks(text)
        all_chunks: list[np.ndarray] = []
        sample_rate = int(getattr(ChatterboxBackend._model, "sr", 24000))
        silence = np.zeros(int(sample_rate * BREAK_SILENCE_SECONDS), dtype=np.float32)
        for i, block in enumerate(blocks):
            if i > 0:
                all_chunks.append(silence)
            wav = ChatterboxBackend._model.generate(block)
            if hasattr(wav, "cpu"):
                wav = wav.cpu().numpy()
            all_chunks.append(np.asarray(wav, dtype=np.float32).reshape(-1))

        if not all_chunks:
            raise ValueError("Chatterbox-TTS generated no audio segments")
        audio_np = np.concatenate(all_chunks) if len(all_chunks) > 1 else all_chunks[0]
        return _to_wav(audio_np, sample_rate=sample_rate)

    def _generate_fallback(self, text: str, meta: dict[str, Any]) -> bytes:
        """Synthesize a safe WAV fallback when models cannot load."""
        sample_rate = 24000
        duration_ms = max(500, min(len(text) * 60, 5000))
        frames = int(sample_rate * (duration_ms / 1000.0))
        samples = [
            0.2 * math.sin(2 * math.pi * 440.0 * i / sample_rate) for i in range(frames)
        ]
        return _to_wav(samples, sample_rate=sample_rate)


def _to_wav(samples: list | Any, sample_rate: int = 24000) -> bytes:
    """Convert normalized audio samples to mono 16-bit WAV bytes."""
    buffer = io.BytesIO()
    flat = list(samples)
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = struct.pack(
            "<" + "h" * len(flat),
            *[max(-32768, min(32767, int(float(sample) * 32767))) for sample in flat],
        )
        handle.writeframes(frames)
    return buffer.getvalue()
