import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from behave import given, then, when


@given("a simulated speech bridge process")
def start_bridge(context):
    context.directory = tempfile.TemporaryDirectory()


@when("it receives capabilities, synthesis, an invalid request, and synthesis")
def send_requests(context):
    first = Path(context.directory.name).resolve() / "first"
    first.mkdir()
    second = Path(context.directory.name).resolve() / "second"
    second.mkdir()
    requests = [
        {"protocol": 1, "id": "one", "op": "capabilities", "voice": "fake:test"},
        {
            "protocol": 1,
            "id": "first",
            "op": "synthesize",
            "text": "Hello",
            "voice": "fake:test",
            "speed": 1,
            "seed": 0,
            "outputDir": str(first),
        },
        {"protocol": 1, "id": "two", "op": "synthesize"},
        {
            "protocol": 1,
            "id": "three",
            "op": "synthesize",
            "text": "Hello",
            "voice": "fake:test",
            "speed": 1,
            "seed": 0,
            "outputDir": str(second),
        },
    ]
    env = dict(
        os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2] / "cli/src")
    )
    context.process = subprocess.run(
        [sys.executable, "-m", "auritus.speech_bridge"],
        input="".join(json.dumps(r) + "\n" for r in requests),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    context.responses = [
        json.loads(line) for line in context.process.stdout.splitlines()
    ]


@then("it returns four correlated JSON responses and exits cleanly")
def check_responses(context):
    assert context.process.returncode == 0, context.process.stderr
    assert [r["id"] for r in context.responses] == ["one", "first", "two", "three"]
    assert context.responses[0]["result"]["ready"]
    assert context.responses[2]["error"]["code"] == "INVALID_REQUEST"
    assert context.responses[1]["ok"] and context.responses[3]["ok"]


@then("the simulated audio and metadata have verified sample counts and digests")
def check_artifacts(context):
    result = context.responses[3]["result"]
    directory = Path(context.directory.name) / "second"
    data = (directory / result["audioPath"]).read_bytes()
    assert json.loads((directory / result["metadataPath"]).read_text()) == result
    assert hashlib.sha256(data).hexdigest() == result["audioSha256"]
    with wave.open(io.BytesIO(data)) as wav:
        assert wav.getnframes() == result["sampleCount"]
        assert (
            hashlib.sha256(wav.readframes(wav.getnframes())).hexdigest()
            == result["pcmSha256"]
        )
    assert result["extensions"]["auritus.simulation"]["simulated"] is True
    context.directory.cleanup()


@given("a simulated local Kokoro cache")
def fake_kokoro_cache(context):
    from unittest.mock import patch
    from auritus import speech_bridge

    context.bridge = speech_bridge
    context.cache = tempfile.TemporaryDirectory()
    context.model = Path(context.cache.name) / ("a" * 40)
    context.voices = Path(context.cache.name) / ("b" * 40)
    context.model.mkdir()
    (context.voices / "voices").mkdir(parents=True)
    (context.model / "config.json").write_text("{}")
    (context.model / "model.safetensors").write_bytes(b"weights")
    (context.voices / "voices" / "af_heart.safetensors").write_bytes(b"voice")
    context.resolver = patch.object(
        speech_bridge,
        "_local_snapshot",
        side_effect=lambda repo: (
            context.voices if repo.startswith("prince-canuma/") else context.model
        ),
    )
    context.resolver.start()


@when("the bridge inspects complete and incomplete cached snapshots")
def inspect_kokoro_cache(context):
    voice = context.bridge.Voice.parse("kokoro:af_heart")

    def inspect():
        return context.bridge._kokoro_readiness(
            voice, "mlx-community/Kokoro-82M-bf16", True
        )

    context.complete = inspect()
    (context.voices / "voices" / "af_heart.safetensors").unlink()
    context.no_voice = inspect()
    (context.voices / "voices" / "af_heart.safetensors").write_bytes(b"voice")
    (context.model / "model.safetensors").unlink()
    context.no_weights = inspect()


@then("it reports readiness only for the complete snapshot")
def verify_kokoro_cache(context):
    assert context.complete == ("a" * 40, "b" * 40, None)
    assert "Voice" in context.no_voice[2]
    assert "weights" in context.no_weights[2]
    context.resolver.stop()
    context.cache.cleanup()


@when("it receives invalid fields and unsafe output paths")
def send_bad_paths(context):
    root = Path(context.directory.name).resolve()
    (root / "occupied").mkdir()
    (root / "occupied" / "speech.wav").write_bytes(b"existing")
    (root / "real").mkdir()
    (root / "link").symlink_to(root / "real", target_is_directory=True)
    base = {
        "protocol": 1,
        "op": "synthesize",
        "text": "Hello",
        "voice": "fake:test",
        "speed": 1,
        "seed": 0,
        "outputDir": str(root / "real"),
    }
    requests = [
        dict(base, id="extra", unexpected=True),
        dict(base, id="missing", outputDir=str(root / "missing")),
        dict(base, id="link", outputDir=str(root / "link")),
        dict(base, id="occupied", outputDir=str(root / "occupied")),
        dict(base, id="speed", speed=0),
    ]
    env = dict(
        os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2] / "cli/src")
    )
    context.process = subprocess.run(
        [sys.executable, "-m", "auritus.speech_bridge"],
        input="".join(json.dumps(r) + "\n" for r in requests),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    context.responses = [
        json.loads(line) for line in context.process.stdout.splitlines()
    ]


@then("each request receives an invalid request response")
def check_bad_paths(context):
    assert context.process.returncode == 0, context.process.stderr
    assert len(context.responses) == 5
    assert all(r["error"]["code"] == "INVALID_REQUEST" for r in context.responses)
    context.directory.cleanup()


@given("an injected simulated synthesis that prints a diagnostic")
def prepare_diagnostic(context):
    context.directory = tempfile.TemporaryDirectory()


@when("a synthesis request runs through the bridge")
def run_diagnostic(context):
    import contextlib
    from unittest.mock import patch
    from auritus import speech_bridge

    request = {
        "protocol": 1,
        "id": "diagnostic",
        "op": "synthesize",
        "text": "Hello",
        "voice": "fake:test",
        "speed": 1,
        "seed": 0,
        "outputDir": str(Path(context.directory.name).resolve()),
    }
    original = speech_bridge.synthesize

    def simulated_synthesis(*args, **kwargs):
        print("model diagnostic")
        return original(*args, **kwargs)

    output, errors = io.StringIO(), io.StringIO()
    with patch.object(
        speech_bridge, "synthesize", side_effect=simulated_synthesis
    ), patch.object(
        sys, "stdin", io.StringIO(json.dumps(request) + "\n")
    ), contextlib.redirect_stdout(
        output
    ), contextlib.redirect_stderr(
        errors
    ):
        context.exit_code = speech_bridge.main()
    context.output, context.errors = output.getvalue(), errors.getvalue()


@then("stdout contains only a valid response and the diagnostic goes to stderr")
def verify_diagnostic(context):
    assert context.exit_code == 0
    assert json.loads(context.output)["ok"]
    assert "model diagnostic" in context.errors
    context.directory.cleanup()


@given("a simulated cached Kokoro request and injected speech result")
def prepare_injected_kokoro(context):
    from auritus import speech_bridge
    from auritus.speech import SpeechOptions, Voice, synthesize

    context.bridge = speech_bridge
    context.directory = tempfile.TemporaryDirectory()
    fake = synthesize("Hello", Voice.parse("fake:test"), SpeechOptions(1, 0))
    from dataclasses import replace

    context.injected = replace(
        fake, provenance={"backend": "kokoro", "model": "test/kokoro"}
    )
    context.request = {
        "text": "Hello",
        "voice": "kokoro:af_heart",
        "speed": 1,
        "seed": 0,
        "outputDir": str(Path(context.directory.name).resolve()),
    }
    context.capabilities = {
        "installed": True,
        "ready": True,
        "modelId": "test/kokoro",
        "modelRevision": "a" * 40,
        "cacheDisabledReason": None,
        "options": {"speed": True},
        "extensions": {"auritus.kokoro": {"voiceRevision": "a" * 40}},
    }


@when("the bridge publishes the injected speech")
def publish_injected_kokoro(context):
    from unittest.mock import patch
    from auritus.tts.kokoro import KokoroBackend

    with patch.object(
        context.bridge, "synthesize", return_value=context.injected
    ), patch.object(KokoroBackend, "_detect_mlx", return_value=False), patch.object(
        context.bridge, "_local_snapshot", return_value=Path("/tmp") / ("a" * 40)
    ):
        context.result = context.bridge._synthesize(
            context.request,
            context.bridge.Voice.parse("kokoro:af_heart"),
            context.capabilities,
        )


@then("the result retains model revision and is marked non-simulated")
def check_injected_kokoro(context):
    assert context.result["provenance"]["modelRevision"] == "a" * 40
    assert context.result["provenance"]["backend"] == "kokoro"
    assert context.result["extensions"]["auritus.simulation"]["simulated"] is False
    data = (Path(context.directory.name) / "speech.wav").read_bytes()
    assert hashlib.sha256(data).hexdigest() == context.result["audioSha256"]
    context.directory.cleanup()


@given("a local-only cache resolver spy")
def prepare_cache_spy(context):
    from unittest.mock import patch

    context.resolver_spy = patch(
        "huggingface_hub.snapshot_download", return_value="/tmp/snapshot"
    )
    context.resolver = context.resolver_spy.start()


@when("the bridge resolves a cached snapshot")
def resolve_cached_snapshot(context):
    from auritus.speech_bridge import _local_snapshot

    context.path = _local_snapshot("test/model")


@then("the resolver requests local files only")
def check_local_only(context):
    context.resolver.assert_called_once_with(
        repo_id="test/model", local_files_only=True
    )
    context.resolver_spy.stop()


@given("two simulated Kokoro snapshots")
def two_snapshots(context):
    from unittest.mock import patch
    from auritus.tts.kokoro import KokoroBackend

    prepare_injected_kokoro(context)
    context.backend_state = patch.multiple(
        KokoroBackend, _model=object(), _local_model_path=None, _local_voice_path=None
    )
    context.backend_state.start()
    context.bindings = []


@when("successive requests select each snapshot")
def bind_snapshots(context):
    from unittest.mock import patch
    from auritus.tts.kokoro import KokoroBackend

    for letter in ("a", "b"):
        directory = Path(context.directory.name).resolve() / letter
        directory.mkdir()
        context.request["outputDir"] = str(directory)
        context.capabilities["modelRevision"] = letter * 40
        context.capabilities["extensions"]["auritus.kokoro"]["voiceRevision"] = (
            letter * 40
        )

        def injected(*args, **kwargs):
            assert (
                KokoroBackend._model is None
            ), "Previous snapshot model was not cleared"
            context.bindings.append(
                (KokoroBackend._local_model_path, KokoroBackend._local_voice_path)
            )
            KokoroBackend._model = object()
            return context.injected

        with patch.object(
            context.bridge, "synthesize", side_effect=injected
        ), patch.object(KokoroBackend, "_detect_mlx", return_value=False), patch.object(
            context.bridge, "_local_snapshot", return_value=Path("/tmp") / (letter * 40)
        ):
            context.bridge._synthesize(
                context.request,
                context.bridge.Voice.parse("kokoro:af_heart"),
                context.capabilities,
            )


@then("each request binds its own model and voice files")
def check_snapshot_bindings(context):
    assert [model.name for model, _ in context.bindings] == ["a" * 40, "b" * 40]
    assert all(voice.parent.parent == model for model, voice in context.bindings)
    context.backend_state.stop()
    context.directory.cleanup()


@given("an injected model that writes directly to stdout")
def prepare_native_diagnostic(context):
    context.directory = tempfile.TemporaryDirectory()


@when("its synthesis request runs in a bridge process")
def run_native_diagnostic(context):
    request = {
        "protocol": 1,
        "id": "native",
        "op": "synthesize",
        "text": "Hello",
        "voice": "fake:test",
        "speed": 1,
        "seed": 0,
        "outputDir": str(Path(context.directory.name).resolve()),
    }
    script = (
        "import os\nfrom auritus import speech_bridge as b\n"
        "original=b.synthesize\n"
        'def injected(*a,**kw):\n os.write(1,b"native diagnostic\\n"); return original(*a,**kw)\n'
        "b.synthesize=injected\nraise SystemExit(b.main())\n"
    )
    env = dict(
        os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2] / "cli/src")
    )
    context.process = subprocess.run(
        [sys.executable, "-c", script],
        input=json.dumps(request) + "\n",
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


@then("the native diagnostic goes to stderr and stdout contains only JSON")
def check_native_diagnostic(context):
    assert context.process.returncode == 0
    assert json.loads(context.process.stdout)["ok"]
    assert "native diagnostic" in context.process.stderr
    context.directory.cleanup()


@given("an empty segment directory and simulated speech")
def empty_segment(context):
    context.directory = tempfile.TemporaryDirectory()


@when("publication fails before its atomic commit")
def fail_publication(context):
    from unittest.mock import patch
    from auritus import speech_bridge

    request = {
        "text": "Hello",
        "speed": 1,
        "seed": 0,
        "outputDir": str(Path(context.directory.name).resolve()),
    }
    voice = speech_bridge.Voice.parse("fake:test")
    with patch.object(
        speech_bridge.os, "replace", side_effect=OSError("injected failure")
    ):
        try:
            speech_bridge._synthesize(
                request, voice, speech_bridge._capabilities(voice)
            )
        except OSError:
            pass
        else:
            raise AssertionError("Expected injected publication failure")


@then("the segment directory has no published artifacts")
def verify_no_partial_publication(context):
    assert list(Path(context.directory.name).iterdir()) == []
    context.directory.cleanup()


def prepare_loader_fixture(context, runtime):
    from unittest.mock import patch
    from auritus.tts.kokoro import KokoroBackend

    context.runtime = runtime
    context.model_path = Path("/tmp/simulated-model")
    context.voice_path = Path(
        "/tmp/simulated-voice." + ("safetensors" if runtime == "mlx" else "pt")
    )
    context.calls = {}
    context.backend_state = patch.multiple(
        KokoroBackend,
        _model=None,
        _local_model_path=context.model_path,
        _local_voice_path=context.voice_path,
    )
    context.backend_state.start()


@given("simulated MLX Kokoro dependencies and selected local paths")
def prepare_mlx_fixture(context):
    prepare_loader_fixture(context, "mlx")


@given("simulated PyTorch Kokoro dependencies and selected local paths")
def prepare_torch_fixture(context):
    prepare_loader_fixture(context, "torch")


@when("the Kokoro backend generates simulated MLX audio")
def run_mlx_loader(context):
    from types import ModuleType, SimpleNamespace
    from unittest.mock import patch
    from auritus.tts.kokoro import KokoroBackend

    class Model:
        def generate(self, text, voice, speed):
            context.calls["generate"] = (text, voice, speed)
            return [SimpleNamespace(audio=[0.1, -0.1])]

    def load_model(path, lazy):
        context.calls["load"] = (path, lazy)
        return Model()

    fake_utils = ModuleType("mlx_audio.tts.utils")
    fake_utils.load_model = load_model
    with patch.dict(sys.modules, {"mlx_audio.tts.utils": fake_utils}):
        context.audio = KokoroBackend()._generate_mlx(
            "Hello", {"voice_id": "af_heart", "speed": 1.25}
        )


@when("the Kokoro backend generates simulated PyTorch audio")
def run_torch_loader(context):
    from types import ModuleType, SimpleNamespace
    from unittest.mock import patch
    from auritus.tts.kokoro import KokoroBackend

    class Model:
        def __init__(self, **kwargs):
            context.calls["model"] = kwargs
            context.calls["model_instance"] = self

        def to(self, device):
            context.calls["device"] = device
            return self

        def eval(self):
            context.calls["eval"] = True
            return self

    class Pipeline:
        def __init__(self, **kwargs):
            context.calls["pipeline"] = kwargs

        def __call__(self, text, voice, speed):
            context.calls["generate"] = (text, voice, speed)
            return [SimpleNamespace(audio=[0.1, -0.1])]

    fake_kokoro = ModuleType("kokoro")
    fake_kokoro.KModel, fake_kokoro.KPipeline = Model, Pipeline
    fake_torch = ModuleType("torch")
    fake_torch.cuda = SimpleNamespace(is_available=lambda: False)
    with patch.dict(sys.modules, {"kokoro": fake_kokoro, "torch": fake_torch}):
        context.audio = KokoroBackend()._generate_torch(
            "Hello", {"voice_id": "af_heart", "speed": 1.25}
        )


@then("the model and voice loaders receive those selected paths")
def check_loader_paths(context):
    if context.runtime == "mlx":
        assert context.calls["load"] == (context.model_path, False)
    else:
        assert context.calls["model"] == {
            "repo_id": "hexgrad/Kokoro-82M",
            "config": str(context.model_path / "config.json"),
            "model": str(context.model_path / "kokoro-v1_0.pth"),
        }
        assert context.calls["device"] == "cpu" and context.calls["eval"]
        assert context.calls["pipeline"]["model"] is context.calls["model_instance"]
        assert context.calls["pipeline"]["device"] == "cpu"
    assert context.calls["generate"] == ("Hello", str(context.voice_path), 1.25)
    with wave.open(io.BytesIO(context.audio)) as wav:
        assert wav.getnframes() == 2
    context.backend_state.stop()
