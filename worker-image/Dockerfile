# GPU worker image for AWS Batch (requires NVIDIA GPU at runtime).
# Local smoke test: docker run --gpus all ...
# Model weights are fetched at runtime (see docs/TTS_LICENSES.md), not baked in.
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/src/
ENV PYTHONPATH=/app/src

ENTRYPOINT ["python3", "-m", "runner"]
