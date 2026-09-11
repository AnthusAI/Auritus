"""Pluggable TTS backends for Auritus workers."""

from __future__ import annotations

from tts.base import TTSBackend
from tts.higgs import HiggsBackend
from tts.qwen import QwenBackend
from tts.registry import get_backend

__all__ = ["TTSBackend", "HiggsBackend", "QwenBackend", "get_backend"]
