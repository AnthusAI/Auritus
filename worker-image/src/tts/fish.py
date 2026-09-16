"""Fish Speech TTS backend for AWS Batch and Linux GPU workers.

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
    "FishBackend",
    "resolve_fish_voice",
]

FISH_DEFAULT_VOICE = "narrator"
FISH_TORCH_MODEL = "fishaudio/fish-speech-1.5"
FISH_MLX_MODEL = "mlx-community/fishaudio-s2-pro-8bit-mlx"

# How long a real silence gap is between AURITUS_BREAK_MARKER-delimited
# blocks for this specific backend/voice. The marker itself and how it's
# split live in tts.breaks, shared by every backend -- only the gap length
# is a per-backend tuning choice.
BREAK_SILENCE_SECONDS = 0.4


def resolve_fish_voice(meta: dict[str, Any]) -> str:
    """Return a Fish Speech voice or reference style name for synthesis.

    :param meta: Job metadata containing an optional ``voice_id``.
    :returns: Voice identifier string.
    """
    raw = meta.get("voice_id")
    if raw is None:
        return FISH_DEFAULT_VOICE
    if isinstance(raw, str) and not raw.strip():
        return FISH_DEFAULT_VOICE
    return str(raw)


class FishBackend(TTSBackend):
    """Fish Speech TTS backend.

    On Apple Silicon: loads mlx-community/fishaudio-s2-pro-8bit-mlx via mlx-audio.
    On Linux / AWS Batch GPU: loads via PyTorch on CUDA with fallback.
    """

    name = "fish"
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
        """Generate speech audio using Fish Speech."""
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if FishBackend._is_mlx is None:
            FishBackend._is_mlx = FishBackend._detect_mlx()

        if FishBackend._is_mlx:
            try:
                return self._generate_mlx(text, meta)
            except Exception:
                return self._generate_fallback(text, meta)

        try:
            return self._generate_torch(text, meta)
        except Exception:
            return self._generate_fallback(text, meta)

    def _generate_mlx(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via mlx-audio on Apple Silicon."""
        import numpy as np

        try:
            import huggingface_hub

            cached = huggingface_hub.try_to_load_from_cache(
                FISH_MLX_MODEL, "model.safetensors"
            )
            if not isinstance(cached, str):
                raise FileNotFoundError(
                    f"Model weights for {FISH_MLX_MODEL} not cached locally"
                )
        except ImportError:
            pass

        from mlx_audio.tts.utils import load_model

        if FishBackend._model is None:
            FishBackend._model = load_model(
                FISH_MLX_MODEL,
                lazy=False,
            )
        sample_rate = int(
            getattr(
                FishBackend._model,
                "sample_rate",
                getattr(FishBackend._model, "sr", 44100),
            )
        )
        blocks = split_on_breaks(text)
        all_chunks: list[np.ndarray] = []
        silence = np.zeros(int(sample_rate * BREAK_SILENCE_SECONDS), dtype=np.float32)

        for i, block in enumerate(blocks):
            if i > 0:
                all_chunks.append(silence)
            gen = FishBackend._model.generate(block)
            block_chunks = [np.array(result.audio) for result in gen]
            if block_chunks:
                all_chunks.extend(block_chunks)

        if not all_chunks:
            raise ValueError("Fish Speech generated no audio segments")
        audio_np = np.concatenate(all_chunks) if len(all_chunks) > 1 else all_chunks[0]
        return _to_wav(audio_np, sample_rate=sample_rate)

    def _generate_torch(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via PyTorch on CUDA."""
        import torch

        if not torch.cuda.is_available():
            return self._generate_fallback(text, meta)

        from fish_speech.api import TTS as FishTTS

        if FishBackend._model is None:
            FishBackend._model = FishTTS()
        audio = FishBackend._model.generate(text)
        samples = audio.tolist() if hasattr(audio, "tolist") else list(audio)
        return _to_wav(samples, sample_rate=44100)

    def _generate_fallback(self, text: str, meta: dict[str, Any]) -> bytes:
        """Synthetic fallback audio for unit testing or environments without GPU weights."""
        sample_rate = 24000
        duration_ms = max(500, min(len(text) * 60, 5000))
        frames = int(sample_rate * (duration_ms / 1000.0))
        samples = [
            0.2 * math.sin(2 * math.pi * 520.0 * i / sample_rate) for i in range(frames)
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
