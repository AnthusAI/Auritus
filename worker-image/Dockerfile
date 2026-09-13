# Worker image for AWS Batch (GPU provided by Batch at runtime).
# Kokoro and Qwen 3 CustomVoice (plus CPU torch) are baked in so Batch jobs
# do not spend their startup window installing synthesizer packages.
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src/
ENV PYTHONPATH=/app/src

ENTRYPOINT ["python3", "-m", "runner"]
