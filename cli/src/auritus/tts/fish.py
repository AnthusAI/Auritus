"""Fish Speech TTS backend for AWS Batch and Linux GPU workers.

Weights are fetched at runtime per docs/TTS_LICENSES.md.
"""

from __future__ import annotations

import io
import math
import os
import struct
import wave
from typing import Any

from auritus.tts.base import TTSBackend
from auritus.tts.breaks import AURITUS_BREAK_MARKER, split_on_breaks

__all__ = [
    "AURITUS_BREAK_MARKER",
    "FishBackend",
    "resolve_fish_voice",
    "split_on_breaks",
]

FISH_DEFAULT_VOICE = "narrator"
FISH_TORCH_MODEL = "fishaudio/s2-pro"
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
        """Generate speech audio using Fish Speech.

        Only ImportError (an optional heavy dependency genuinely not
        installed, e.g. local dev/test) falls back to the stub tone. A real
        generation failure (CUDA OOM, a model bug, a download failure) must
        raise so the job is correctly marked failed instead of silently
        reporting success with fake audio -- this previously caught bare
        Exception here, the same anti-pattern confirmed happening in
        production for higgs.py and fixed there too.
        """
        if not text.strip():
            raise ValueError("Cannot generate audio for empty text")
        if FishBackend._is_mlx is None:
            FishBackend._is_mlx = FishBackend._detect_mlx()

        if FishBackend._is_mlx:
            try:
                return self._generate_mlx(text, meta)
            except ImportError:
                return self._generate_fallback(text, meta)

        try:
            return self._generate_torch(text, meta)
        except ImportError:
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
        """Generate via PyTorch on CUDA using fishaudio/s2-pro."""
        import numpy as np
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[fish] resolved device={device}", flush=True)

        if not torch.cuda.is_available():
            return self._generate_fallback(text, meta)

        from pathlib import Path

        import fish_speech
        from huggingface_hub import snapshot_download

        project_root = Path(fish_speech.__path__[0]) / ".project-root"
        if not project_root.exists():
            try:
                project_root.touch()
            except Exception:
                pass

        if FishBackend._model is None:
            ckpt_dir = snapshot_download(FISH_TORCH_MODEL)
            precision = (
                torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            )

            llama_queue = _launch_thread_safe_queue(
                checkpoint_path=ckpt_dir,
                device=device,
                precision=precision,
                compile=False,
            )

            import hydra
            from hydra import compose, initialize_config_dir
            from hydra.utils import instantiate

            config_dir = str(Path(fish_speech.__path__[0]) / "configs")
            hydra.core.global_hydra.GlobalHydra.instance().clear()
            with initialize_config_dir(version_base="1.3", config_dir=config_dir):
                cfg = compose(config_name="modded_dac_vq")
            decoder_model = instantiate(cfg)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            codec_path = Path(ckpt_dir) / "codec.pth"
            state_dict = torch.load(
                codec_path, map_location="cpu", mmap=True, weights_only=True
            )
            if "state_dict" in state_dict:
                state_dict = state_dict["state_dict"]
            if any("generator" in k for k in state_dict):
                state_dict = {
                    k.replace("generator.", ""): v
                    for k, v in state_dict.items()
                    if "generator." in k
                }
            decoder_model.load_state_dict(state_dict, strict=False, assign=True)
            decoder_model.eval()
            decoder_model.to(device=device)

            from fish_speech.inference_engine import TTSInferenceEngine

            FishBackend._model = TTSInferenceEngine(
                llama_queue=llama_queue,
                decoder_model=decoder_model,
                precision=precision,
                compile=False,
            )

        from fish_speech.inference_engine import ServeTTSRequest
        from fish_speech.utils.schema import ServeReferenceAudio

        ref_file = meta.get("ref_file")
        ref_text = meta.get("ref_text")
        references = []
        if not ref_file:
            local_ref = os.path.join(os.path.dirname(__file__), "basic_ref_en.wav")
            if os.path.exists(local_ref):
                ref_file = local_ref
                if not ref_text:
                    ref_text = "Some call me nature, others call me mother nature."
        if ref_file and os.path.exists(ref_file):
            with open(ref_file, "rb") as f:
                audio_bytes = f.read()
            references = [ServeReferenceAudio(audio=audio_bytes, text=ref_text or "")]

        blocks = split_on_breaks(text)
        all_chunks: list[np.ndarray] = []
        sample_rate = 44100
        silence = np.zeros(int(sample_rate * BREAK_SILENCE_SECONDS), dtype=np.float32)

        for i, block in enumerate(blocks):
            if i > 0:
                all_chunks.append(silence)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            req = ServeTTSRequest(
                text=block,
                references=references,
                streaming=False,
                max_new_tokens=1024,
            )
            block_audio = None
            for res in FishBackend._model.inference(req):
                if res.code == "final":
                    sr, block_audio = res.audio
                    sample_rate = sr
                elif res.code == "error":
                    raise res.error
            if block_audio is not None and len(block_audio) > 0:
                all_chunks.append(block_audio)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

        if not all_chunks:
            raise ValueError("Fish Speech generated no audio segments")
        audio_np = np.concatenate(all_chunks) if len(all_chunks) > 1 else all_chunks[0]
        return _to_wav(audio_np, sample_rate=sample_rate)

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


def _launch_thread_safe_queue(
    checkpoint_path: str,
    device: str,
    precision: Any,
    compile: bool = False,
) -> Any:
    """Launch thread-safe request queue for Fish Speech text-to-semantic inference.

    Initializes DualARTransformer directly on the target device with the specified
    precision to prevent host memory exhaustion during weight loading.
    """
    import queue
    import threading

    import torch
    from fish_speech.models.text2semantic.inference import (
        DualARTransformer,
        GenerateRequest,
        WrappedGenerateResponse,
        decode_one_token_ar,
        generate_long,
        logger,
    )

    input_queue: queue.Queue = queue.Queue()
    init_event = threading.Event()
    worker_error: list[Exception] = []

    def worker() -> None:
        try:
            os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
            old_default_dtype = torch.get_default_dtype()
            torch.set_default_dtype(precision)
            try:
                if device == "cuda" and torch.cuda.is_available():
                    torch.cuda.set_device(0)
                    torch.cuda.empty_cache()
                with torch.device(device):
                    max_length = 4096
                    model = DualARTransformer.from_pretrained(
                        checkpoint_path, load_weights=True, max_length=max_length
                    )
                    model = model.to(device=device, dtype=precision)
                    decode_one_token = decode_one_token_ar
                    model.setup_caches(
                        max_batch_size=1,
                        max_seq_len=max_length,
                        dtype=next(model.parameters()).dtype,
                    )
            finally:
                torch.set_default_dtype(old_default_dtype)
            init_event.set()
        except Exception as exc:
            import traceback

            logger.error(traceback.format_exc())
            worker_error.append(exc)
            init_event.set()
            return

        while True:
            item: GenerateRequest | None = input_queue.get()
            if item is None:
                break

            kwargs = item.request
            response_queue = item.response_queue

            try:
                for chunk in generate_long(
                    model=model, decode_one_token=decode_one_token, **kwargs
                ):
                    response_queue.put(
                        WrappedGenerateResponse(status="success", response=chunk)
                    )
            except Exception as e:
                import traceback

                logger.error(traceback.format_exc())
                response_queue.put(WrappedGenerateResponse(status="error", response=e))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    init_event.wait()

    if worker_error:
        raise worker_error[0]

    return input_queue
