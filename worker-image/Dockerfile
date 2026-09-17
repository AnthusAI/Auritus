# Worker image for AWS Batch (GPU provided by Batch at runtime).
# All supported TTS synthesizer packages are pre-baked so Batch jobs
# do not spend their startup window installing packages at runtime.
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    libgomp1 \
    libsndfile1 \
    sox \
    libsox-dev \
    libsox-fmt-all \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Main virtualenv for Kokoro, Chatterbox, F5-TTS, Higgs (Torch 2.6.0, Transformers 5.x)
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /opt/venv-main && \
    /opt/venv-main/bin/pip install --no-cache-dir -r /app/requirements.txt

# 2. Dedicated virtualenv for Qwen (strictly requires transformers 4.57.x and torch 2.5.1)
COPY requirements-qwen.txt /app/requirements-qwen.txt
RUN python3 -m venv /opt/venv-qwen && \
    /opt/venv-qwen/bin/pip install --no-cache-dir -r /app/requirements-qwen.txt

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY src/ /app/src/
ENV PYTHONPATH=/app/src

ENTRYPOINT ["/app/entrypoint.sh"]
