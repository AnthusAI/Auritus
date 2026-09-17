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
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Main virtualenv for Kokoro & Chatterbox (Torch 2.6.0, Transformers 5.2.0)
COPY requirements.txt /app/requirements.txt
RUN python3 -m venv /opt/venv-main && \
    /opt/venv-main/bin/pip install --no-cache-dir -r /app/requirements.txt

# 2. Dedicated virtualenv for F5-TTS
COPY requirements-f5.txt /app/requirements-f5.txt
RUN python3 -m venv /opt/venv-f5 && \
    /opt/venv-f5/bin/pip install --no-cache-dir -r /app/requirements-f5.txt

# 3. Dedicated virtualenv for Qwen (strictly requires transformers 4.57.x and torch 2.5.1)
COPY requirements-qwen.txt /app/requirements-qwen.txt
RUN python3 -m venv /opt/venv-qwen && \
    /opt/venv-qwen/bin/pip install --no-cache-dir -r /app/requirements-qwen.txt

# 4. Dedicated virtualenv for Higgs (requires transformers>=5.5.0 for native higgs_audio_v2_tokenizer)
COPY requirements-higgs.txt /app/requirements-higgs.txt
RUN python3 -m venv /opt/venv-higgs && \
    /opt/venv-higgs/bin/pip install --no-cache-dir -r /app/requirements-higgs.txt

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY src/ /app/src/
ENV PYTHONPATH=/app/src

ENTRYPOINT ["/app/entrypoint.sh"]
