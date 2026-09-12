# Worker image for AWS Batch (GPU provided by Batch at runtime).
# ML packages (torch, kokoro) are installed at runtime when a job starts.
# Build tools (gcc, make) are included so pip can install torch from wheels,
# not compile from source (which takes 20+ minutes).
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir httpx numpy

COPY src/ /app/src/
ENV PYTHONPATH=/app/src

ENTRYPOINT ["python3", "-m", "runner"]
