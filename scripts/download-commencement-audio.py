#!/usr/bin/env python3
"""Utility to download and extract Steve Jobs commencement address reference audio.

Downloads the 2005 Stanford Commencement Address audio from public archive CDN,
extracts a clean, normalized 24 kHz mono WAV reference clip for zero-shot voice
cloning, and writes an accompanying transcript.

Audio assets are saved to the gitignored ``voices/`` directory.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

DEFAULT_AUDIO_URL = (
    "https://audio.podigee-cdn.net/1539-m-86fce7541d53a4ce40d3418d4fbd4aff.mp3"
)
DEFAULT_OUTPUT_DIR = Path("voices")
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_CLIP_START = 464.0
DEFAULT_CLIP_DURATION = 10.5
DEFAULT_CLIP_TRANSCRIPT = (
    "The only way to do great work is to love what you do. "
    "If you haven't found it yet, keep looking."
)


def has_ffmpeg() -> bool:
    """Check whether ffmpeg is available on the system executable path.

    :returns: True if ffmpeg binary is found in PATH.
    """
    return shutil.which("ffmpeg") is not None


def download_audio(url: str, target_path: Path) -> Path:
    """Download audio file from a remote URL to local destination.

    :param url: Remote audio URL.
    :param target_path: Destination local file path.
    :returns: Resolved target Path.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout.write(f"Downloading {url}\n  -> {target_path} ... ")
    sys.stdout.flush()

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Auritus-Voice-Downloader/1.0"},
    )
    with urllib.request.urlopen(request) as response, open(target_path, "wb") as out:
        shutil.copyfileobj(response, out)

    size_mb = target_path.stat().st_size / (1024 * 1024)
    sys.stdout.write(f"done ({size_mb:.2f} MB)\n")
    sys.stdout.flush()
    return target_path


def extract_reference_wav(
    source_audio: Path,
    output_wav: Path,
    start_seconds: float = DEFAULT_CLIP_START,
    duration_seconds: float = DEFAULT_CLIP_DURATION,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> Path:
    """Extract a mono WAV clip from source audio using ffmpeg.

    :param source_audio: Source input audio file.
    :param output_wav: Output WAV file path.
    :param start_seconds: Offset into source audio in seconds.
    :param duration_seconds: Duration of the trimmed clip in seconds.
    :param sample_rate: Target sampling rate in Hz.
    :returns: Resolved output Path.
    """
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start_seconds),
        "-t",
        str(duration_seconds),
        "-i",
        str(source_audio),
        "-ar",
        str(sample_rate),
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(output_wav),
    ]
    sys.stdout.write(
        f"Extracting reference WAV ({duration_seconds}s @ {sample_rate}Hz) ... "
    )
    sys.stdout.flush()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg extraction failed: {result.stderr}")

    sys.stdout.write(f"done ({output_wav})\n")
    sys.stdout.flush()
    return output_wav


def convert_full_wav(
    source_audio: Path,
    output_wav: Path,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> Path:
    """Convert entire audio file to mono 16-bit WAV.

    :param source_audio: Source input audio file.
    :param output_wav: Destination WAV file path.
    :param sample_rate: Sampling frequency in Hz.
    :returns: Resolved destination Path.
    """
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_audio),
        "-ar",
        str(sample_rate),
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(output_wav),
    ]
    sys.stdout.write(f"Converting full recording to WAV @ {sample_rate}Hz ... ")
    sys.stdout.flush()
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {result.stderr}")

    sys.stdout.write(f"done ({output_wav})\n")
    sys.stdout.flush()
    return output_wav


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser for audio downloader.

    :returns: Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Download Steve Jobs commencement speech audio for zero-shot voice cloning.",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_AUDIO_URL,
        help="Source audio download URL.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Target directory for voice files (default: voices).",
    )
    parser.add_argument(
        "--voice-id",
        default="steve_jobs",
        help="Base identifier for reference output files (default: steve_jobs).",
    )
    parser.add_argument(
        "--sample-rate",
        "-r",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        help="Target sampling rate for extracted WAV in Hz (default: 24000).",
    )
    parser.add_argument(
        "--clip-start",
        type=float,
        default=DEFAULT_CLIP_START,
        help="Start timestamp in seconds for reference clip extraction (default: 464.0).",
    )
    parser.add_argument(
        "--clip-duration",
        type=float,
        default=DEFAULT_CLIP_DURATION,
        help="Duration in seconds for reference clip extraction (default: 12.0).",
    )
    parser.add_argument(
        "--full-wav",
        action="store_true",
        help="Also convert the full speech into a complete mono WAV file.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading if raw source file already exists locally.",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    """Execute download and reference clip extraction workflow.

    :param argv: Optional command line argument list.
    :returns: Process exit status code (0 for success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    voice_id = args.voice_id
    raw_source = out_dir / f"{voice_id}_full.mp3"
    ref_wav = out_dir / f"{voice_id}.wav"
    ref_txt = out_dir / f"{voice_id}.txt"
    full_wav = out_dir / f"{voice_id}_full.wav"

    if not (args.skip_download and raw_source.exists()):
        download_audio(args.url, raw_source)
    else:
        sys.stdout.write(f"Using existing raw source: {raw_source}\n")

    if has_ffmpeg():
        extract_reference_wav(
            source_audio=raw_source,
            output_wav=ref_wav,
            start_seconds=args.clip_start,
            duration_seconds=args.clip_duration,
            sample_rate=args.sample_rate,
        )

        ref_txt.write_text(DEFAULT_CLIP_TRANSCRIPT.strip() + "\n", encoding="utf-8")
        sys.stdout.write(f"Wrote reference transcript -> {ref_txt}\n")

        if args.full_wav:
            convert_full_wav(
                source_audio=raw_source,
                output_wav=full_wav,
                sample_rate=args.sample_rate,
            )
    else:
        sys.stdout.write(
            "Note: ffmpeg is not installed on PATH. "
            f"Saved raw audio to {raw_source}.\n"
            "Install ffmpeg to extract normalized WAV clips.\n"
        )

    sys.stdout.write("Voice assets ready in gitignored directory:\n")
    sys.stdout.write(f"  Audio:      {ref_wav if has_ffmpeg() else raw_source}\n")
    if has_ffmpeg():
        sys.stdout.write(f"  Transcript: {ref_txt}\n")
    return 0


if __name__ == "__main__":
    sys.exit(run())
