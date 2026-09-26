#!/bin/bash
set -e

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

BACKEND="${AURITUS_TTS_BACKEND:-${TTS_BACKEND:-kokoro}}"

# AURITUS_MODE=render: a host's own SpeechRenderer deployment submitted one
# request (AURITUS_RENDER_REQUEST); run auritus.render instead of the API
# runner, in the virtualenv for the requested backend.
MODULE="runner"
if [ "${AURITUS_MODE:-}" = "render" ]; then
    MODULE="auritus.render"
fi

if [ "$BACKEND" = "qwen" ] && [ -d "/opt/venv-qwen" ]; then
    exec /opt/venv-qwen/bin/python3 -m "$MODULE" "$@"
elif [ "$BACKEND" = "f5" ] && [ -d "/opt/venv-f5" ]; then
    exec /opt/venv-f5/bin/python3 -m "$MODULE" "$@"
elif [ "$BACKEND" = "higgs" ] && [ -d "/opt/venv-higgs" ]; then
    exec /opt/venv-higgs/bin/python3 -m "$MODULE" "$@"
elif [ "$BACKEND" = "fish" ] && [ -d "/opt/venv-fish" ]; then
    exec /opt/venv-fish/bin/python3 -m "$MODULE" "$@"
else
    exec /opt/venv-main/bin/python3 -m "$MODULE" "$@"
fi
