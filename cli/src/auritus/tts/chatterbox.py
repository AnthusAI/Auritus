"""Chatterbox-TTS (Resemble AI) backend (MLX on Apple Silicon).

Weights are fetched at runtime from Hugging Face (mlx-community/chatterbox-fp16).
See ``docs/TTS_LICENSES.md`` for license and fetch policy.
"""

from __future__ import annotations

import io
import math
import struct
import wave
from typing import Any

from auritus.tts.base import TTSBackend

CHATTERBOX_DEFAULT_VOICE = "default"
CHATTERBOX_MLX_MODEL = "mlx-community/chatterbox-fp16"

AURITUS_BREAK_MARKER = "[[auritus:break]]"
BREAK_SILENCE_SECONDS = 0.4


def split_on_breaks(text: str) -> list[str]:
    """Split TTS input into segments on the block-boundary pause marker.

    :param text: Full TTS input, possibly containing AURITUS_BREAK_MARKER.
    :returns: Non-empty, trimmed segments in original order.
    """
    segments = [s.strip() for s in text.split(AURITUS_BREAK_MARKER)]
    return [s for s in segments if s]


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
    """Chatterbox-TTS backend using mlx-audio on Apple Silicon.

    Loads mlx-community/chatterbox-fp16 at runtime via mlx-audio.
    Falls back to a safe synthesized WAV on non-Apple platforms.
    """

    name = "chatterbox"
    _model = None
    _is_mlx = None

    @classmethod
    def _detect_mlx(cls) -> bool:
        """Detect whether MLX is available on this platform.

        :returns: True if running on Apple Silicon Darwin.
        """
        import platform

        if platform.system() != "Darwin":
            return False
        machine = platform.machine().lower()
        return machine.startswith(("arm", "aarch"))

    def generate(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate speech audio using Chatterbox-TTS.

        On Apple Silicon: uses mlx-audio (fast, native MLX).
        On other platforms: falls back to safe synthesized audio.

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
        return self._generate_fallback(text, meta)

    def _generate_mlx(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via mlx-audio (Apple Silicon).

        :param text: TTS input text.
        :param meta: Job metadata.
        :returns: WAV audio bytes.
        """
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

    def _generate_fallback(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate audio on non-Apple platforms or fallback.

        :param text: TTS input text.
        :param meta: Job metadata.
        :returns: WAV audio bytes.
        """
        sample_rate = 24000
        duration_ms = max(500, min(len(text) * 60, 5000))
        frames = int(sample_rate * (duration_ms / 1000.0))
        samples = [
            0.2 * math.sin(2 * math.pi * 440.0 * i / sample_rate) for i in range(frames)
        ]
        return _to_wav(samples, sample_rate=sample_rate)


def _to_wav(samples: list | Any, sample_rate: int = 24000) -> bytes:
    """Convert normalized audio samples to mono 16-bit WAV bytes.

    :param samples: Audio amplitude samples.
    :param sample_rate: Audio sampling frequency in Hz.
    :returns: Serialized mono 16-bit WAV bytes.
    """
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
