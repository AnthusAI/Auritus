"""Versioned offline NDJSON adapter for :mod:`auritus.speech`."""

from __future__ import annotations

import contextlib
import hashlib
import io
import importlib.util
import json
import math
import os
import re
import sys
import tempfile
import wave
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from auritus import __version__
from auritus.speech import SpeechOptions, UnsupportedOption, Voice, synthesize
from auritus.tts import get_backend
from auritus.tts.base import BackendUnavailable
from auritus.tts.breaks import parse_voiced_segments


class BridgeError(Exception):
    """A recoverable request error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _validate(request: object) -> dict:
    if not isinstance(request, dict):
        raise ValueError("Request must be an object")
    if request.get("protocol") != 1 or isinstance(request.get("protocol"), bool):
        raise ValueError("Unsupported protocol")
    if not isinstance(request.get("id"), str) or not request["id"]:
        raise ValueError("Request id must be a nonempty string")
    operation = request.get("op")
    allowed = {"protocol", "id", "op", "voice", "voicesDir"}
    if operation == "synthesize":
        allowed |= {"text", "speed", "seed", "outputDir"}
        for key in ("text", "voice", "outputDir"):
            if not isinstance(request.get(key), str) or not request[key].strip():
                raise BridgeError("INVALID_REQUEST", f"{key} must be a nonempty string")
        speed, seed = request.get("speed"), request.get("seed")
        if (
            isinstance(speed, bool)
            or not isinstance(speed, (int, float))
            or not math.isfinite(speed)
            or speed <= 0
        ):
            raise BridgeError(
                "INVALID_REQUEST", "speed must be a positive finite number"
            )
        if (
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or not 0 <= seed <= 4294967295
        ):
            raise BridgeError(
                "INVALID_REQUEST", "seed must be an unsigned 32-bit integer"
            )
    elif operation != "capabilities":
        raise BridgeError("INVALID_REQUEST", "Unknown operation")
    if set(request) - allowed:
        raise BridgeError("INVALID_REQUEST", "Unknown request fields")
    for key in ("voice", "voicesDir"):
        if key in request and (
            not isinstance(request[key], str) or not request[key].strip()
        ):
            raise BridgeError("INVALID_REQUEST", f"{key} must be a nonempty string")
    if "voicesDir" in request and not Path(request["voicesDir"]).is_dir():
        raise BridgeError("INVALID_REQUEST", "voicesDir must be an existing directory")
    return request


def _local_snapshot(repository: str) -> Path:
    from huggingface_hub import snapshot_download

    return Path(snapshot_download(repo_id=repository, local_files_only=True))


def _kokoro_readiness(
    voice: Voice, model_id: str, mlx: bool
) -> tuple[str | None, str | None, str | None]:
    voice_id = "af_heart" if voice.id == "default" else voice.id
    if not re.fullmatch(r"[A-Za-z0-9_]+", voice_id):
        return None, None, "Voice id is not a supported single Kokoro voice"
    try:
        model = _local_snapshot(model_id)
        voice_repo = "prince-canuma/Kokoro-82M" if mlx else model_id
        voices = _local_snapshot(voice_repo)
        config = model / "config.json"
        if not config.is_file() or not isinstance(json.loads(config.read_text()), dict):
            raise ValueError("Model config is missing or invalid")
        weights = (
            list(model.glob("*.safetensors")) + list(model.glob("*.npz"))
            if mlx
            else [model / "kokoro-v1_0.pth"]
        )
        if not weights or any(
            not p.is_file() or p.stat().st_size == 0 for p in weights
        ):
            raise ValueError("Model weights are missing or empty")
        voice_file = voices / "voices" / f"{voice_id}.{'safetensors' if mlx else 'pt'}"
        if not voice_file.is_file() or voice_file.stat().st_size == 0:
            raise ValueError(f"Voice {voice_id} is missing or empty")
        if not re.fullmatch(r"[0-9a-f]{40}", model.name) or not re.fullmatch(
            r"[0-9a-f]{40}", voices.name
        ):
            raise ValueError("Cached snapshot revision is unavailable")
        return model.name, voices.name, None
    except Exception as exc:
        return None, None, f"Local Kokoro cache unavailable: {exc}"


def _capabilities(voice: Voice) -> dict:
    try:
        backend = get_backend(voice.backend)
    except ValueError as exc:
        raise BridgeError("BACKEND_UNAVAILABLE", str(exc)) from exc
    simulated = backend.name == "fake"
    model_id = backend.model_id()
    revision = None
    voice_revision = None
    reason = None
    if simulated:
        installed, ready = True, True
        reason = "Simulated backend has no immutable model revision"
    elif backend.name == "kokoro":
        from auritus.tts.kokoro import KokoroBackend

        mlx = KokoroBackend._detect_mlx()
        modules = (
            ("mlx_audio", "mlx", "huggingface_hub", "misaki", "spacy", "en_core_web_sm")
            if mlx
            else (
                "kokoro",
                "torch",
                "huggingface_hub",
                "misaki",
                "spacy",
                "en_core_web_sm",
            )
        )
        installed = all(importlib.util.find_spec(name) is not None for name in modules)
        if installed:
            revision, voice_revision, reason = _kokoro_readiness(voice, model_id, mlx)
        else:
            reason = "Required Kokoro runtime libraries are not installed"
        ready = installed and reason is None
    else:
        modules = {
            "higgs": "mlx_audio",
            "qwen": "qwen_tts",
            "fish": "fish_speech",
            "f5": "f5_tts",
            "chatterbox": "chatterbox",
            "coqui": "TTS",
            "bark": "transformers",
        }
        module = modules.get(backend.name)
        if (
            backend.name in ("higgs", "qwen", "fish", "f5", "chatterbox")
            and backend._detect_mlx()
        ):
            module = "mlx_audio"
        installed = bool(module and importlib.util.find_spec(module))
        ready = False
        reason = "Offline loading is not verified for this backend"
    cache_reason = (
        None
        if ready and revision and voice_revision == revision
        else (
            "Voice snapshot revision is separate from model revision"
            if ready and revision
            else "Model revision is unavailable"
        )
    )
    extensions = {"auritus.simulation": {"simulated": simulated}}
    if reason:
        extensions["auritus.readiness"] = {"reason": reason}
    if voice_revision:
        extensions["auritus.kokoro"] = {"voiceRevision": voice_revision}
    return {
        "installed": installed,
        "ready": ready,
        "backend": backend.name,
        "modelId": model_id,
        "modelRevision": revision,
        "auritusVersion": __version__,
        "voice": str(voice),
        "voices": [],
        "options": {
            "speed": backend.supports_speed,
            "seed": True,
            "referenceAudio": backend.name in ("fish", "f5", "chatterbox"),
            "phonemes": False,
        },
        "cacheDisabledReason": cache_reason,
        "extensions": extensions,
    }


def _synthesize(request: dict, voice: Voice, capabilities: dict) -> dict:
    if not capabilities["installed"]:
        raise BridgeError(
            "BACKEND_UNAVAILABLE",
            capabilities["extensions"]["auritus.readiness"]["reason"],
        )
    if not capabilities["ready"]:
        raise BridgeError(
            "MODEL_NOT_INSTALLED",
            capabilities["extensions"]["auritus.readiness"]["reason"],
        )
    if request["speed"] != 1 and not capabilities["options"]["speed"]:
        raise BridgeError("UNSUPPORTED_OPTION", "Backend does not support speed")
    if voice.backend == "kokoro":
        for _, block_voice in parse_voiced_segments(request["text"], voice.id):
            if block_voice != voice.id:
                raise BridgeError(
                    "INVALID_REQUEST",
                    "Inline voice changes are not supported by the bridge",
                )
    directory = Path(request["outputDir"])
    if not directory.is_dir() or any(
        part.is_symlink() for part in (directory, *directory.parents)
    ):
        raise BridgeError(
            "INVALID_REQUEST", "outputDir must be an existing non-symlink directory"
        )
    targets = [directory / "speech.wav", directory / "speech.json"]
    if any(path.exists() or path.is_symlink() for path in targets):
        raise BridgeError(
            "INVALID_REQUEST", "outputDir already contains speech artifacts"
        )
    if voice.backend == "kokoro":
        from auritus.tts.kokoro import KokoroBackend
        import spacy.cli

        def deny_download(*args, **kwargs):
            raise BridgeError(
                "MODEL_NOT_INSTALLED", "Automatic language model downloads are disabled"
            )

        spacy.cli.download = deny_download
        mlx = KokoroBackend._detect_mlx()
        snapshot = _local_snapshot(capabilities["modelId"])
        voice_repo = "prince-canuma/Kokoro-82M" if mlx else capabilities["modelId"]
        voice_snapshot = _local_snapshot(voice_repo)
        if (
            snapshot.name != capabilities["modelRevision"]
            or voice_snapshot.name
            != capabilities["extensions"]["auritus.kokoro"]["voiceRevision"]
        ):
            raise BridgeError(
                "MODEL_NOT_INSTALLED", "Model or voice snapshot changed during request"
            )
        voice_id = "af_heart" if voice.id == "default" else voice.id
        voice_path = (
            voice_snapshot / "voices" / f"{voice_id}.{'safetensors' if mlx else 'pt'}"
        )
        if (
            KokoroBackend._local_model_path != snapshot
            or KokoroBackend._local_voice_path != voice_path
        ):
            KokoroBackend._model = None
            KokoroBackend._local_model_path = snapshot
            KokoroBackend._local_voice_path = voice_path
    speech = synthesize(
        request["text"],
        voice,
        SpeechOptions(request["speed"], request["seed"]),
        voices_dir=request.get("voicesDir"),
    )
    with wave.open(io.BytesIO(speech.wav), "rb") as wav:
        count, rate = wav.getnframes(), wav.getframerate()
        pcm = wav.readframes(count)
    result = {
        "audioPath": "speech.wav",
        "metadataPath": "speech.json",
        "audioSha256": hashlib.sha256(speech.wav).hexdigest(),
        "pcmSha256": hashlib.sha256(pcm).hexdigest(),
        "sampleRate": rate,
        "sampleCount": count,
        "durationSec": count / rate,
        "segments": [
            {"text": s.text, "startSec": s.start, "endSec": s.end}
            for s in speech.segments
        ],
        "provenance": {
            "backend": speech.provenance["backend"],
            "modelId": speech.provenance["model"],
            "modelRevision": capabilities["modelRevision"],
            "auritusVersion": __version__,
            "voice": str(voice),
            "speed": request["speed"],
            "seed": request["seed"],
            "referenceAudioSha256": None,
            "referenceTranscriptSha256": None,
            "cacheDisabledReason": capabilities["cacheDisabledReason"],
            "extensions": (
                {"auritus.kokoro": capabilities["extensions"]["auritus.kokoro"]}
                if "auritus.kokoro" in capabilities["extensions"]
                else {}
            ),
            "requestKey": speech.request_key,
            "contentHash": None,
        },
        "extensions": {"auritus.simulation": {"simulated": voice.backend == "fake"}},
    }
    if any(directory.iterdir()):
        raise BridgeError("INVALID_REQUEST", "outputDir must be empty")
    staging = Path(tempfile.mkdtemp(prefix=".auritus-speech-", dir=directory.parent))
    try:
        for name, data in (
            ("speech.wav", speech.wav),
            ("speech.json", json.dumps(result, ensure_ascii=False).encode("utf-8")),
        ):
            with (staging / name).open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        os.replace(staging, directory)
    finally:
        if staging.exists():
            for path in staging.iterdir():
                path.unlink()
            staging.rmdir()
    return result


@contextlib.contextmanager
def _redirect_native_stdout():
    sys.stdout.flush()
    saved = os.dup(1)
    try:
        os.dup2(2, 1)
        yield
    finally:
        os.dup2(saved, 1)
        os.close(saved)


def main() -> int:
    """Serve requests until EOF; return nonzero for fatal protocol errors."""
    for line in sys.stdin:
        try:
            request = json.loads(line)
            _validate(request)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"Fatal protocol error: {exc}", file=sys.stderr)
            return 1
        except BridgeError as exc:
            response = {
                "protocol": 1,
                "id": request["id"],
                "ok": False,
                "error": {"code": exc.code, "message": str(exc)},
            }
        else:
            try:
                with _redirect_native_stdout(), contextlib.redirect_stdout(sys.stderr):
                    voice = Voice.parse(request.get("voice", "kokoro:af_heart"))
                    capabilities = _capabilities(voice)
                    result = (
                        capabilities
                        if request["op"] == "capabilities"
                        else _synthesize(request, voice, capabilities)
                    )
                response = {
                    "protocol": 1,
                    "id": request["id"],
                    "ok": True,
                    "result": result,
                }
            except Exception as exc:
                code = (
                    exc.code
                    if isinstance(exc, BridgeError)
                    else (
                        "UNSUPPORTED_OPTION"
                        if isinstance(exc, UnsupportedOption)
                        else (
                            "BACKEND_UNAVAILABLE"
                            if isinstance(exc, BackendUnavailable)
                            else "SYNTHESIS_FAILED"
                        )
                    )
                )
                response = {
                    "protocol": 1,
                    "id": request["id"],
                    "ok": False,
                    "error": {"code": code, "message": str(exc) or type(exc).__name__},
                }
        print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
