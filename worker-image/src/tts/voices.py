"""Reference voices for zero-shot cloning (Chatterbox, F5-TTS, Fish-Speech).

A reference voice is ``<id>.wav`` (or another audio format) plus the
``<id>.txt`` transcript of what it says, in one folder the caller names: the
``voices_dir`` argument, or else the ``AURITUS_VOICES`` environment variable.
Nothing else is searched, and there are no aliases, so which recording a
voice id means is always visible from the folder itself.
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "list_voices",
    "resolve_reference_audio",
    "resolve_reference_text",
    "voices_directory",
]

_AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
#: ``<id>_full.<ext>`` holds an untrimmed source recording, not a voice.
_SOURCE_SUFFIX = "_full"


def voices_directory(voices_dir: str | Path | None = None) -> Path | None:
    """The folder reference voices come from.

    :param voices_dir: Folder named by the caller.
    :returns: ``voices_dir``, else ``$AURITUS_VOICES``, else None (no voices).
    """
    if voices_dir:
        return Path(voices_dir)
    env = os.environ.get("AURITUS_VOICES", "").strip()
    return Path(env) if env else None


def list_voices(voices_dir: str | Path | None = None) -> list[str]:
    """Voice ids available in the voices folder, sorted.

    :param voices_dir: Folder named by the caller (see :func:`voices_directory`).
    :returns: One id per reference recording; empty when there is no folder.
    """
    directory = voices_directory(voices_dir)
    if directory is None or not directory.is_dir():
        return []
    return sorted(
        {
            path.stem
            for path in directory.iterdir()
            if path.suffix.lower() in _AUDIO_EXTENSIONS
            and path.is_file()
            and not path.stem.endswith(_SOURCE_SUFFIX)
        }
    )


def resolve_reference_audio(
    voice_id: str,
    voices_dir: str | Path | None = None,
) -> Path | None:
    """Find the reference recording for a voice.

    :param voice_id: Voice id (``"serious"``, matched lowercase), or a path
        to an audio file.
    :param voices_dir: Folder named by the caller (see :func:`voices_directory`).
    :returns: The recording's path, or None if the folder has no such voice.
    """
    if voice_id.strip() and os.path.isfile(voice_id.strip()):
        return Path(voice_id.strip()).resolve()
    clean_id = voice_id.strip().lower()
    if not clean_id:
        return None
    directory = voices_directory(voices_dir)
    if directory is None:
        return None
    for ext in _AUDIO_EXTENSIONS:
        candidate = directory / f"{clean_id}{ext}"
        if candidate.is_file():
            return candidate.resolve()
    return None


def resolve_reference_text(
    voice_id: str,
    voices_dir: str | Path | None = None,
) -> str | None:
    """Read the transcript of a voice's reference recording.

    :param voice_id: Voice id.
    :param voices_dir: Folder named by the caller (see :func:`voices_directory`).
    :returns: The transcript, or None if the folder has none for this voice.
    """
    clean_id = voice_id.strip().lower()
    directory = voices_directory(voices_dir)
    if not clean_id or directory is None:
        return None
    candidate = directory / f"{clean_id}.txt"
    try:
        return candidate.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
