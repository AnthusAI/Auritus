"""Tests for pluggable TTS backends."""

from __future__ import annotations

from pathlib import Path

from auritus.tts import get_backend
from auritus.tts.chatterbox import resolve_chatterbox_voice
from auritus.tts.f5 import resolve_f5_voice
from auritus.tts.fish import resolve_fish_voice
from auritus.tts.higgs import resolve_higgs_voice
from auritus.tts.kokoro import resolve_kokoro_voice
from auritus.tts.qwen import resolve_qwen_voice


def test_higgs_backend_name_and_generate() -> None:
    higgs = get_backend("higgs")
    assert higgs.name == "higgs"
    assert get_backend("higgs-v3").name == "higgs"
    assert get_backend("higgs3").name == "higgs"


def test_higgs_resolve_voice_defaults_to_default() -> None:
    assert resolve_higgs_voice({}) == "default"
    assert resolve_higgs_voice({"voice_id": ""}) == "default"
    assert resolve_higgs_voice({"voice_id": "default"}) == "default"
    assert resolve_higgs_voice({"voice_id": "voice_a"}) == "voice_a"


def test_higgs_backend_empty_text_raises() -> None:
    import pytest

    higgs = get_backend("higgs")
    with pytest.raises(ValueError, match="Cannot generate audio for empty text"):
        higgs.generate("", {})


def test_qwen_backend_resolves_without_generate() -> None:
    qwen = get_backend("qwen")
    assert qwen.name == "qwen"


def test_kokoro_backend_resolves_without_generate() -> None:
    kokoro = get_backend("kokoro")
    assert kokoro.name == "kokoro"


def test_f5_backend_resolves_without_generate() -> None:
    f5 = get_backend("f5")
    assert f5.name == "f5"
    f5_alias = get_backend("f5-tts")
    assert f5_alias.name == "f5"


def test_kokoro_resolve_voice_defaults_to_af_heart() -> None:
    assert resolve_kokoro_voice({}) == "af_heart"
    assert resolve_kokoro_voice({"voice_id": "default"}) == "af_heart"
    assert resolve_kokoro_voice({"voice_id": "am_adam"}) == "am_adam"


def test_qwen_resolve_voice_defaults_to_ryan() -> None:
    assert resolve_qwen_voice({}) == "Ryan"
    assert resolve_qwen_voice({"voice_id": "default"}) == "Ryan"
    assert resolve_qwen_voice({"voice_id": "Chelsie"}) == "Ryan"
    assert resolve_qwen_voice({"voice_id": "Aiden"}) == "Aiden"


def test_f5_resolve_voice_defaults_to_default() -> None:
    assert resolve_f5_voice({}) == "default"
    assert resolve_f5_voice({"voice_id": ""}) == "default"
    assert resolve_f5_voice({"voice_id": "default"}) == "default"
    assert resolve_f5_voice({"voice_id": "custom_voice"}) == "custom_voice"


def test_chatterbox_backend_resolves_without_generate() -> None:
    chatterbox = get_backend("chatterbox")
    assert chatterbox.name == "chatterbox"
    alias = get_backend("chatterbox-tts")
    assert alias.name == "chatterbox"


def test_chatterbox_resolve_voice_defaults_to_default() -> None:
    assert resolve_chatterbox_voice({}) == "default"
    assert resolve_chatterbox_voice({"voice_id": ""}) == "default"
    assert resolve_chatterbox_voice({"voice_id": "default"}) == "default"
    assert resolve_chatterbox_voice({"voice_id": "ref_voice"}) == "ref_voice"


def test_chatterbox_backend_empty_text_raises() -> None:
    import pytest

    chatterbox = get_backend("chatterbox")
    with pytest.raises(ValueError, match="Cannot generate audio for empty text"):
        chatterbox.generate("", {})


def test_fish_backend_resolves_without_generate() -> None:
    fish = get_backend("fish")
    assert fish.name == "fish"


def test_fish_resolve_voice_defaults_to_narrator() -> None:
    assert resolve_fish_voice({}) == "narrator"
    assert resolve_fish_voice({"voice_id": ""}) == "narrator"
    assert resolve_fish_voice({"voice_id": "default"}) == "default"
    assert resolve_fish_voice({"voice_id": "custom"}) == "custom"


def test_fish_backend_empty_text_raises() -> None:
    import pytest

    fish = get_backend("fish")
    with pytest.raises(ValueError, match="Cannot generate audio for empty text"):
        fish.generate("", {})


def test_unknown_backend_raises() -> None:
    try:
        get_backend("nope")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_parse_voiced_segments() -> None:
    from auritus.tts.breaks import parse_voiced_segments

    assert parse_voiced_segments("Hello world", "default") == [
        ("Hello world", "default")
    ]

    text = (
        "Opening narrator. [[auritus:break]] "
        "[[auritus:voice:am_adam]] Lincoln speaking. [[auritus:voice:reset]] "
        "[[auritus:break]] Closing narrator."
    )
    segments = parse_voiced_segments(text, "af_heart")
    assert len(segments) == 3
    assert segments[0] == ("Opening narrator.", "af_heart")
    assert segments[1] == ("Lincoln speaking.", "am_adam")
    assert segments[2] == ("Closing narrator.", "af_heart")


def test_resolve_reference_audio_and_text(tmp_path: Path) -> None:
    from auritus.tts.voices import resolve_reference_audio, resolve_reference_text

    assert resolve_reference_audio("") is None
    assert resolve_reference_audio("nonexistent_voice_xyz_123") is None
    assert resolve_reference_text("") is None
    assert resolve_reference_text("nonexistent_voice_xyz_123") is None

    mock_audio = tmp_path / "mock_voice.wav"
    mock_audio.touch()
    mock_text = tmp_path / "mock_voice.txt"
    mock_text.write_text("sample reference transcript")

    resolved_audio = resolve_reference_audio("mock_voice", search_dirs=[tmp_path])
    assert resolved_audio is not None
    assert resolved_audio.is_file()

    resolved_text = resolve_reference_text("mock_voice", search_dirs=[tmp_path])
    assert resolved_text is not None
    assert "sample reference transcript" in resolved_text

    mock_steve_audio = tmp_path / "steve_jobs.wav"
    mock_steve_audio.touch()
    mock_steve_text = tmp_path / "steve_jobs.txt"
    mock_steve_text.write_text("steve jobs reference transcript")

    assert (
        resolve_reference_audio("steve", search_dirs=[tmp_path])
        == mock_steve_audio.resolve()
    )
    assert (
        resolve_reference_text("steve", search_dirs=[tmp_path])
        == "steve jobs reference transcript"
    )
    assert (
        resolve_reference_audio("steve_jobs", search_dirs=[tmp_path])
        == mock_steve_audio.resolve()
    )
    assert (
        resolve_reference_text("steve_jobs", search_dirs=[tmp_path])
        == "steve jobs reference transcript"
    )


def test_fish_to_wav_normalization() -> None:
    import io
    import wave
    import numpy as np
    from auritus.tts.fish import _to_wav

    low_arr = np.array([-0.3, 0.0, 0.3], dtype=np.float32)
    wav_bytes = _to_wav(low_arr, sample_rate=24000)
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        expected_peak = int(0.85 * 32767)
        assert abs(int(data.max()) - expected_peak) <= 2

    low_list = [-0.2, 0.1, 0.2]
    wav_bytes_list = _to_wav(low_list, sample_rate=24000)
    with wave.open(io.BytesIO(wav_bytes_list), "rb") as wf:
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        assert abs(int(data.max()) - expected_peak) <= 2

    high_arr = np.array([-0.8, 0.0, 0.8], dtype=np.float32)
    wav_bytes_high = _to_wav(high_arr, sample_rate=24000)
    with wave.open(io.BytesIO(wav_bytes_high), "rb") as wf:
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        expected_high = int(0.8 * 32767)
        assert abs(int(data.max()) - expected_high) <= 2

    zero_arr = np.zeros(100, dtype=np.float32)
    wav_bytes_zero = _to_wav(zero_arr, sample_rate=24000)
    with wave.open(io.BytesIO(wav_bytes_zero), "rb") as wf:
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
        assert data.max() == 0
        assert data.min() == 0
