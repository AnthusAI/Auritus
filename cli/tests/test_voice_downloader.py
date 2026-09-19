"""Tests for the commencement speech reference audio download utility."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPT_PATH = (
    Path(__file__).parent.parent.parent / "scripts" / "download-commencement-audio.py"
)


@pytest.fixture
def downloader_module():
    """Dynamically load the download-commencement-audio script module."""
    spec = importlib.util.spec_from_file_location(
        "download_commencement_audio", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_parser_defaults(downloader_module) -> None:
    """Verify default parser configurations and arguments."""
    parser = downloader_module.build_parser()
    args = parser.parse_args([])
    assert "podigee" in args.url
    assert args.output_dir == Path("voices")
    assert args.voice_id == "steve_jobs"
    assert args.sample_rate == 24000
    assert args.clip_start == 464.0
    assert args.clip_duration == 12.0
    assert args.full_wav is False


def test_extract_reference_wav_command(downloader_module, tmp_path: Path) -> None:
    """Verify ffmpeg is called with correct arguments for WAV extraction."""
    source = tmp_path / "source.mp3"
    source.write_bytes(b"dummy")
    target = tmp_path / "out.wav"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        downloader_module.extract_reference_wav(
            source_audio=source,
            output_wav=target,
            start_seconds=10.0,
            duration_seconds=5.0,
            sample_rate=24000,
        )

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-ss" in cmd
        assert "10.0" in cmd
        assert "-t" in cmd
        assert "5.0" in cmd
        assert "-ar" in cmd
        assert "24000" in cmd
        assert "-ac" in cmd
        assert "1" in cmd


def test_run_workflow_with_mocks(downloader_module, tmp_path: Path) -> None:
    """Verify run executes download and extraction workflow in target dir."""
    out_dir = tmp_path / "custom_voices"

    with patch.object(downloader_module, "download_audio") as mock_dl:
        mock_dl.side_effect = lambda url, target: target.write_bytes(b"dummy_mp3")
        with patch.object(downloader_module, "has_ffmpeg", return_value=True):
            with patch.object(
                downloader_module, "extract_reference_wav"
            ) as mock_extract:
                mock_extract.side_effect = lambda **kwargs: kwargs[
                    "output_wav"
                ].write_bytes(b"dummy_wav")
                status = downloader_module.run(
                    [
                        "--output-dir",
                        str(out_dir),
                        "--voice-id",
                        "jobs_test",
                    ]
                )

                assert status == 0
                mock_dl.assert_called_once()
                mock_extract.assert_called_once()
                txt_file = out_dir / "jobs_test.txt"
                assert txt_file.exists()
                assert "Don't settle" in txt_file.read_text(encoding="utf-8")
