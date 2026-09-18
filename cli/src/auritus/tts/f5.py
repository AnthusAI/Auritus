"""F5-TTS backend (non-autoregressive flow matching, MLX on Apple Silicon)."""

from __future__ import annotations

import io
import struct
import wave
from typing import Any

from auritus.tts.base import TTSBackend

F5_DEFAULT_VOICE = "default"
F5_MLX_MODEL = "mlx-community/F5-TTS"


def resolve_f5_voice(meta: dict[str, Any]) -> str:
    """Return an F5 voice or reference style name for synthesis.

    :param meta: Job metadata containing an optional ``voice_id``.
    :returns: Voice identifier string.
    """
    raw = meta.get("voice_id")
    if raw is None:
        return F5_DEFAULT_VOICE
    if isinstance(raw, str) and not raw.strip():
        return F5_DEFAULT_VOICE
    return str(raw)


class F5Backend(TTSBackend):
    """F5-TTS backend using mlx-audio on Apple Silicon.

    Loads mlx-community/F5-TTS at runtime via mlx-audio or f5-tts-mlx.
    Falls back to PyTorch f5-tts on non-Apple platforms.
    """

    name = "f5"
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
        """Generate speech audio using F5-TTS.

        On Apple Silicon: uses mlx-audio (fast, native MLX).
        On other platforms: falls back to PyTorch f5-tts.

        :param text: TTS input text.
        :param meta: Job metadata (voice_id, name, byline).
        :returns: WAV audio bytes at 24000 Hz mono 16-bit.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if F5Backend._is_mlx is None:
            F5Backend._is_mlx = F5Backend._detect_mlx()

        if F5Backend._is_mlx:
            return self._generate_mlx(text, meta)
        return self._generate_torch(text, meta)

    def _generate_mlx(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via f5-tts-mlx (Apple Silicon).

        :param text: TTS input text.
        :param meta: Job metadata.
        :returns: WAV audio bytes.
        """
        import os
        import tempfile
        from f5_tts_mlx.generate import generate as f5_gen
        from auritus.tts.voices import (
            resolve_reference_audio,
            resolve_reference_text,
        )

        voice = resolve_f5_voice(meta)
        ref_audio = resolve_reference_audio(voice)
        ref_text = resolve_reference_text(voice) or ""

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            gen_kwargs: dict[str, Any] = {
                "generation_text": text,
                "output_path": tmp_path,
                "steps": 8,
            }
            if ref_audio:
                gen_kwargs["ref_audio_path"] = str(ref_audio)
                gen_kwargs["ref_audio_text"] = ref_text
            f5_gen(**gen_kwargs)
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _generate_torch(self, text: str, meta: dict[str, Any]) -> bytes:
        """Generate via PyTorch f5-tts (fallback for non-Apple).

        :param text: TTS input text.
        :param meta: Job metadata.
        :returns: WAV audio bytes.
        """
        import numpy as np
        from f5_tts.api import F5TTS

        if F5Backend._model is None:
            F5Backend._model = F5TTS()
        voice = resolve_f5_voice(meta)
        _ = voice
        wav, sr, _ = F5Backend._model.infer(text=text)
        audio_np = np.array(wav).reshape(-1)
        return _to_wav(audio_np, sample_rate=int(sr) if sr else 24000)


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
