"""Auritus: just-in-time text-to-speech, and an embeddable speech library.

The library surface is re-exported here; see :mod:`auritus.speech`.
"""

__version__ = "0.26.0"

from auritus.speech import (  # noqa: E402 - speech reads __version__ above
    Segment,
    Speech,
    SpeechOptions,
    UnsupportedOption,
    Voice,
    request_key,
    synthesize,
)

__all__ = [
    "Segment",
    "Speech",
    "SpeechOptions",
    "UnsupportedOption",
    "Voice",
    "__version__",
    "request_key",
    "synthesize",
]
