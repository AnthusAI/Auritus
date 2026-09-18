#!/bin/bash
set -e

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

BACKEND="${AURITUS_TTS_BACKEND:-${TTS_BACKEND:-kokoro}}"

if [ "$BACKEND" = "qwen" ] && [ -d "/opt/venv-qwen" ]; then
    exec /opt/venv-qwen/bin/python3 -m runner "$@"
elif [ "$BACKEND" = "f5" ] && [ -d "/opt/venv-f5" ]; then
    exec /opt/venv-f5/bin/python3 -m runner "$@"
elif [ "$BACKEND" = "higgs" ] && [ -d "/opt/venv-higgs" ]; then
    exec /opt/venv-higgs/bin/python3 -m runner "$@"
elif [ "$BACKEND" = "fish" ] && [ -d "/opt/venv-fish" ]; then
    exec /opt/venv-fish/bin/python3 -m runner "$@"
else
    exec /opt/venv-main/bin/python3 -m runner "$@"
fi
