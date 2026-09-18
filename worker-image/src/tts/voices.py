"""Voice reference audio and transcript discovery utilities.

Discovers local and pre-baked voice assets for zero-shot voice cloning
across supported TTS backends (Chatterbox, F5-TTS, Fish-Speech).
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "resolve_reference_audio",
    "resolve_reference_text",
]

_AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")


def _get_candidate_directories(
    custom_dirs: list[Path] | None = None,
) -> list[Path]:
    """Return an ordered list of directories to inspect for voice assets.

    :param custom_dirs: Optional custom search directories.
    :returns: List of existing directory paths to inspect.
    """
    candidates: list[Path] = []
    if custom_dirs:
        candidates.extend(custom_dirs)

    current_dir = Path.cwd()
    candidates.append(current_dir / "voices")
    candidates.append(current_dir)

    module_dir = Path(__file__).resolve().parent
    candidates.append(module_dir)

    for parent in Path(__file__).resolve().parents:
        repo_voices = parent / "voices"
        if repo_voices.is_dir():
            candidates.append(repo_voices)

    container_voices = Path("/app/voices")
    if container_voices.is_dir():
        candidates.append(container_voices)

    unique: list[Path] = []
    seen: set[str] = set()
    for directory in candidates:
        try:
            resolved = directory.resolve()
            path_str = str(resolved)
            if path_str not in seen and resolved.is_dir():
                seen.add(path_str)
                unique.append(resolved)
        except (OSError, PermissionError):
            continue
    return unique


def resolve_reference_audio(
    voice_id: str,
    search_dirs: list[Path] | None = None,
) -> Path | None:
    """Find a reference audio file for a given voice identifier.

    :param voice_id: Voice identifier string (e.g. ``"serious"``, ``"steve_jobs"``).
    :param search_dirs: Optional list of directory paths to search.
    :returns: Path to the reference audio file, or None if not found.
    """
    clean_id = voice_id.strip().lower()
    if not clean_id:
        return None

    if os.path.isfile(voice_id):
        return Path(voice_id).resolve()

    directories = _get_candidate_directories(search_dirs)
    for directory in directories:
        for ext in _AUDIO_EXTENSIONS:
            candidate = directory / f"{clean_id}{ext}"
            if candidate.is_file():
                return candidate.resolve()
    return None


def resolve_reference_text(
    voice_id: str,
    search_dirs: list[Path] | None = None,
) -> str | None:
    """Find and read a reference transcript for a given voice identifier.

    :param voice_id: Voice identifier string.
    :param search_dirs: Optional list of directory paths to search.
    :returns: Reference transcript string if found, otherwise None.
    """
    clean_id = voice_id.strip().lower()
    if not clean_id:
        return None

    directories = _get_candidate_directories(search_dirs)
    for directory in directories:
        candidate = directory / f"{clean_id}.txt"
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeDecodeError):
                continue
    return None
