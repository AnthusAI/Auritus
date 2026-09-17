"""Higgs Audio v3 (Boson AI) TTS backend for AWS Batch and Linux GPU workers.

Weights are fetched at runtime (not baked into the Docker image) per docs/TTS_LICENSES.md.
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
    "HiggsBackend",
    "resolve_higgs_voice",
]

HIGGS_DEFAULT_VOICE = "default"
HIGGS_TORCH_MODEL = "multimodalart/higgs-audio-v3-tts-4b-transformers"

# How long a real silence gap is between AURITUS_BREAK_MARKER-delimited
# blocks for this specific backend/voice. The marker itself and how it's
# split live in tts.breaks, shared by every backend -- only the gap length
# is a per-backend tuning choice.
BREAK_SILENCE_SECONDS = 0.5


def resolve_higgs_voice(meta: dict[str, Any]) -> str:
    """Return a Higgs voice or reference style name for synthesis.

    :param meta: Job metadata containing an optional ``voice_id``.
    :returns: Voice identifier string.
    """
    raw = meta.get("voice_id")
    if raw is None:
        return HIGGS_DEFAULT_VOICE
    if isinstance(raw, str) and not raw.strip():
        return HIGGS_DEFAULT_VOICE
    return str(raw)


class HiggsBackend(TTSBackend):
    """Higgs Audio v3 TTS backend.

    On Apple Silicon: loads bosonai/higgs-audio-v3-tts-4b via mlx-audio.
    On Linux / AWS Batch GPU: loads Higgs v3 via transformers/PyTorch on CUDA.
    """

    name = "higgs"
    _model = None
    _tokenizer = None
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
        """Generate speech audio using Higgs Audio v3.

        :param text: TTS input text.
        :param meta: Job metadata (voice_id, name, byline).
        :returns: WAV audio bytes at 24000 Hz mono 16-bit.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if HiggsBackend._is_mlx is None:
            HiggsBackend._is_mlx = HiggsBackend._detect_mlx()

        if HiggsBackend._is_mlx:
            return self._generate_mlx(text, meta)
        return self._generate_torch(text, meta)

    def _generate_mlx(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via mlx-audio on Apple Silicon."""
        import numpy as np
        from mlx_audio.tts.utils import load_model

        if HiggsBackend._model is None:
            HiggsBackend._model = load_model(
                "bosonai/higgs-audio-v3-tts-4b",
                lazy=False,
            )
        voice = resolve_higgs_voice(meta)
        _ = voice
        sample_rate = int(getattr(HiggsBackend._model, "sample_rate", 24000))
        blocks = split_on_breaks(text)
        all_chunks: list[np.ndarray] = []
        silence = np.zeros(int(sample_rate * BREAK_SILENCE_SECONDS), dtype=np.float32)
        for i, block in enumerate(blocks):
            if i > 0:
                all_chunks.append(silence)
            gen = HiggsBackend._model.generate(block)
            block_chunks = [np.array(result.audio) for result in gen]
            if block_chunks:
                all_chunks.extend(block_chunks)
        if not all_chunks:
            raise ValueError("Higgs Audio v3 generated no audio segments")
        audio_np = np.concatenate(all_chunks) if len(all_chunks) > 1 else all_chunks[0]
        return _to_wav(audio_np, sample_rate=sample_rate)

    def _generate_torch(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via PyTorch / transformers on CUDA for AWS Batch."""
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            if HiggsBackend._model is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
                HiggsBackend._tokenizer = AutoTokenizer.from_pretrained(
                    HIGGS_TORCH_MODEL
                )
                HiggsBackend._model = (
                    AutoModelForCausalLM.from_pretrained(
                        HIGGS_TORCH_MODEL,
                        trust_remote_code=True,
                        torch_dtype=dtype,
                    )
                    .to(device)
                    .eval()
                )

            voice = resolve_higgs_voice(meta)
            _ = voice
            blocks = split_on_breaks(text)
            sample_rate = 24000
            silence = [0.0] * int(sample_rate * BREAK_SILENCE_SECONDS)
            all_samples: list[float] = []
            for block in blocks:
                if all_samples:
                    all_samples.extend(silence)
                wav = HiggsBackend._model.generate_speech(
                    block, HiggsBackend._tokenizer
                )
                audio_np = wav.detach().cpu().numpy().reshape(-1)
                all_samples.extend(audio_np.tolist())
            if not all_samples:
                raise ValueError("Higgs Audio v3 generated no audio segments")
            return _to_wav(all_samples, sample_rate=sample_rate)
        except ImportError:
            # Only a missing optional dependency (e.g. local dev/test
            # without the runtime-installed package) is a legitimate reason
            # to stub. This previously caught bare Exception, which meant a
            # real generation failure (CUDA OOM, a model bug, a download
            # failure) silently produced a normal-looking 'done' job with a
            # fake 440Hz tone -- confirmed happening in production. Let real
            # errors propagate so the job is correctly marked failed.
            sample_rate = 24000
            duration_ms = max(500, min(len(text) * 60, 5000))
            frames = int(sample_rate * (duration_ms / 1000.0))
            samples = [
                0.2 * math.sin(2 * math.pi * 440.0 * i / sample_rate)
                for i in range(frames)
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
