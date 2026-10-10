"""Auritus: just-in-time text-to-speech, and an embeddable speech library.

The library surface is re-exported here; see :mod:`auritus.speech`.
"""

__version__ = "1.0.0"

from auritus.speech import (  # noqa: E402 - speech reads __version__ above
    BackendUnavailable,
    Segment,
    Speech,
    SpeechOptions,
    UnsupportedOption,
    Voice,
    VoiceNotFound,
    request_key,
    synthesize,
)

__all__ = [
    "BackendUnavailable",
    "Segment",
    "Speech",
    "SpeechOptions",
    "UnsupportedOption",
    "Voice",
    "VoiceNotFound",
    "__version__",
    "request_key",
    "synthesize",
]
