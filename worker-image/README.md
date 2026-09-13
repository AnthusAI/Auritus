# Auritus GPU worker image

Container entrypoint for the AWS Batch fallback path. A Step Functions workflow
submits one job per content hash after the local-worker claim window expires.

## GPU requirement

Built from [NVIDIA CUDA runtime](https://hub.docker.com/r/nvidia/cuda) on
Ubuntu 22.04. Batch job definitions request one GPU; the image expects an
NVIDIA driver on the host (Batch EC2 GPU instances or `docker run --gpus all`
for local experiments).

TTS backends load model weights at runtime; they are not redistributed inside
this image. See `docs/TTS_LICENSES.md`.

## Environment

The runner reads (aliases in parentheses for CDK / Step Functions):

| Variable | Purpose |
| --- | --- |
| `API_URL` (`AURITUS_API_ENDPOINT`) | Auritus HTTP API base URL |
| `JOB_HASH` (`AURITUS_CONTENT_HASH`) | Job content hash |
| `JOB_TOKEN` (`AURITUS_JOB_TOKEN`) | Single-job bearer token |
| `TTS_BACKEND` (`AURITUS_TTS_BACKEND`) | Default backend if the job row omits one |

Optional: `AWS_BATCH_JOB_ID` (used in the claim owner id).

## Flow

1. POST `/jobs/{hash}/redeem` with the job token (falls back to the token as bearer if redeem is not deployed).
2. PUT `/jobs/{hash}/claim` with `claim_owner`.
3. Load the requested TTS backend from `src/tts/registry.py` (default `kokoro`).
4. POST `/jobs/{hash}/presign-upload`, PUT audio to S3, PUT `/jobs/{hash}/done`.
5. On failure, PUT `/jobs/{hash}/failed` when available.

## Build

```bash
docker build -t auritus-worker:latest worker-image/
```

## Layout

- `src/runner.py` — Batch entrypoint
- `src/tts/base.py` — `TTSBackend` ABC
- `src/tts/higgs.py`, `src/tts/qwen.py` — pluggable backends
- `src/tts/kokoro.py` — Kokoro speech via PyTorch
- `src/tts/qwen.py` — Qwen 3 CustomVoice via PyTorch on Linux Batch
- `src/tts/registry.py` — backend selection by name
