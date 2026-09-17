#!/bin/bash
set -e

BACKEND="${AURITUS_TTS_BACKEND:-${TTS_BACKEND:-kokoro}}"

if [ "$BACKEND" = "qwen" ] && [ -d "/opt/venv-qwen" ]; then
    exec /opt/venv-qwen/bin/python3 -m runner "$@"
elif [ "$BACKEND" = "f5" ] && [ -d "/opt/venv-f5" ]; then
    exec /opt/venv-f5/bin/python3 -m runner "$@"
else
    exec /opt/venv-main/bin/python3 -m runner "$@"
fi
