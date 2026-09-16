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

        if FishBackend._model is None:
            FishBackend._model = _load_fish_mlx_model(FISH_MLX_MODEL)
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
    try:
        import numpy as np

        if isinstance(samples, np.ndarray):
            clamped = np.clip(samples, -1.0, 1.0)
            frames = (clamped * 32767.0).astype(np.int16).tobytes()
        else:
            flat = list(samples)
            frames = struct.pack(
                "<" + "h" * len(flat),
                *[
                    max(-32768, min(32767, int(float(sample) * 32767)))
                    for sample in flat
                ],
            )
    except ImportError:
        flat = list(samples)
        frames = struct.pack(
            "<" + "h" * len(flat),
            *[max(-32768, min(32767, int(float(sample) * 32767))) for sample in flat],
        )
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(frames)
    return buffer.getvalue()


def _load_fish_mlx_model(repo_id: str) -> Any:
    """Load Fish Speech MLX model with proper weight remapping.

    :param repo_id: Hugging Face model repository identifier.
    :returns: Fully initialized and loaded FishSpeech Model instance.
    """
    import mlx.core as mx
    from mlx_audio.tts.models.fish_qwen3_omni.config import ModelConfig
    from mlx_audio.tts.models.fish_qwen3_omni.fish_speech import Model
    from mlx_audio.utils import apply_quantization, get_model_path, load_config

    path = get_model_path(repo_id)
    config = load_config(path)
    model_config = ModelConfig.from_dict(config)
    model = Model(model_config)

    weights = mx.load(str(path / "model.safetensors"))
    remapped = {}
    for key, value in weights.items():
        if key.startswith("model."):
            remapped[key] = value
        elif key.startswith("text_model.model."):
            new_key = key[len("text_model.model.") :]
            remapped[f"model.{new_key}"] = value
        elif key.startswith("audio_decoder."):
            suffix = key[len("audio_decoder.") :]
            if suffix.startswith("codebook_embeddings."):
                new_key = suffix
            else:
                new_key = f"fast_{suffix}"
            remapped[f"model.{new_key}"] = value
        else:
            remapped[f"model.{key}"] = value

    apply_quantization(model, config, remapped, None)
    model.load_weights(list(remapped.items()), strict=True)
    mx.eval(model.parameters())
    model.eval()

    Model.post_load_hook(model, path)
    return model
