"""Reference voices for zero-shot cloning (Chatterbox, F5-TTS, Fish-Speech).

A reference voice is ``<id>.wav`` (or another audio format) plus the
``<id>.txt`` transcript of what it says, in one folder the caller names: the
``voices_dir`` argument, or else the ``AURITUS_VOICES`` environment variable.
Nothing else is searched, and there are no aliases, so which recording a
voice id means is always visible from the folder itself.

A voice the request names must be found: :func:`require_reference_audio`
raises :class:`VoiceNotFound` rather than letting a backend speak in a
stock voice instead. Only a request for the backend's default voice may go
without a recording.
"""

from __future__ import annotations

import os
from collections.abc import Collection
from pathlib import Path

__all__ = [
    "VoiceNotFound",
    "list_voices",
    "require_reference_audio",
    "resolve_reference_audio",
    "resolve_reference_text",
    "voices_directory",
]

_AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".ogg", ".m4a")
#: ``<id>_full.<ext>`` holds an untrimmed source recording, not a voice.
_SOURCE_SUFFIX = "_full"


class VoiceNotFound(ValueError):
    """A request named a voice that has no reference recording.

    Raised instead of speaking in a stock voice, so a job that asked for one
    voice can never succeed in another.

    :param voice_id: The voice the request named.
    :param directory: The voices folder that was searched, or None when no
        folder was configured.
    """

    def __init__(self, voice_id: str, directory: Path | None) -> None:
        if directory is None:
            where = (
                "no voices folder is configured "
                "(pass voices_dir or set AURITUS_VOICES)"
            )
        elif not directory.is_dir():
            where = f"the voices folder {directory} does not exist"
        else:
            names = ", ".join(
                f"{voice_id.strip().lower()}{ext}" for ext in _AUDIO_EXTENSIONS
            )
            where = f"the voices folder {directory} has none of {names}"
        super().__init__(
            f"Voice {voice_id!r} was requested but has no reference recording: "
            f"{where}. Refusing to substitute a stock voice."
        )
        self.voice_id = voice_id
        self.directory = directory


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


def require_reference_audio(
    voice_id: str,
    voices_dir: str | Path | None = None,
    *,
    default_voice_ids: Collection[str],
) -> Path | None:
    """Find the reference recording a request needs, or refuse.

    :param voice_id: Voice id the request resolved to.
    :param voices_dir: Folder named by the caller (see :func:`voices_directory`).
    :param default_voice_ids: Ids that mean "the backend's default voice";
        matched case-insensitively. An empty id is always a default request.
    :returns: The recording's path; None only for a default-voice request
        with no recording, which the backend speaks in its stock voice.
    :raises VoiceNotFound: If a named voice has no recording.
    """
    reference = resolve_reference_audio(voice_id, voices_dir)
    if reference is not None:
        return reference
    clean_id = voice_id.strip().lower()
    if not clean_id or clean_id in {v.lower() for v in default_voice_ids}:
        return None
    raise VoiceNotFound(voice_id, voices_directory(voices_dir))
