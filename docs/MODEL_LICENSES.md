# TTS model licenses (research notes)

This document tracks license posture for the TTS backends Auritus ships. It is
not legal advice. Confirm each row with counsel before redistributing weights or
shipping a public worker image.

**Weight strategy:** fetch model weights at runtime from Hugging Face cache or
an operator-controlled mirror. The Batch image may install pip wheels
(`kokoro`, `qwen-tts`). Do not bake weight blobs into the git tree or Docker
build context.

Recorded 13 September 2026.

| Backend | Vendor / model | License (provisional) | Redistributable weights? | Image-baked weights | Runtime-fetch weights | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| Kokoro | hexgrad/Kokoro-82M | Apache-2.0 on the [model card](https://huggingface.co/hexgrad/Kokoro-82M) | Yes under Apache-2.0, with attribution; **espeak-ng GPLv3** may apply if that G2P is linked | Wheels only (`kokoro==0.9.4`) | **Required** | Card cited 13 Sep 2026 |
| Qwen 3 | Qwen3-TTS-12Hz-1.7B-CustomVoice | Apache-2.0 on the [model card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice) and [qwen-tts](https://pypi.org/project/qwen-tts/0.1.1/) | Yes under Apache-2.0, with attribution | Wheels only (`qwen-tts==0.1.1`) | **Required** | Card cited 13 Sep 2026 |
| Higgs | bosonai/higgs-audio-v3-tts-4b | Boson Research & Non-Commercial | Non-commercial only (Boson license) | Not in image build | **Required** | Card cited 15 Sep 2026 |
| F5-TTS | SWivid/F5-TTS, mlx-community/F5-TTS | MIT on the [model card](https://huggingface.co/SWivid/F5-TTS) and code | Yes under MIT | Wheels only | **Required** | Card cited 14 Sep 2026 |

## Kokoro

- **License name:** Apache-2.0 for weights in `hexgrad/Kokoro-82M`.
- **Redistributability:** weights may be used and redistributed under Apache-2.0.
  Operators who ship a binary that links **espeak-ng** must account for GPLv3.
- **Recommended strategy:** runtime-fetch via the `kokoro` package Hugging Face
  download; pin `kokoro==0.9.4` in `worker-image/requirements.txt`.
- **Operator checklist:** keep Apache notices; decide whether the worker host
  installs espeak-ng.

## Qwen 3

- **License name:** Apache-2.0 for CustomVoice weights and `qwen-tts` code.
- **Redistributability:** weights and code under Apache-2.0 with attribution.
- **Recommended strategy:** runtime-fetch of `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`
  (and tokenizer) on the GPU worker; keep blobs out of `worker-image/` context.
- **Operator checklist:** retain Apache notices; pin `qwen-tts==0.1.1`.

## Higgs (Boson)

- **License name:** Boson Higgs TTS 3 Research and Non-Commercial License Agreement.
- **Redistributability:** Weights are licensed for research and non-commercial use.
  Do not redistribute or bake weights into public ECR or Docker Hub images. Operators
  must obtain commercial terms from Boson AI for commercial deployments.
- **Recommended strategy:** runtime-fetch `bosonai/higgs-audio-v3-tts-4b` via `mlx-audio`
  on Apple Silicon or `multimodalart/higgs-audio-v3-tts-4b-transformers` via PyTorch/CUDA
  on AWS Batch.
- **Operator checklist:** retain Boson license notice; ensure weights are downloaded
  at runtime into scratch storage; verify non-commercial compliance or secure commercial license.

## F5-TTS

- **License name:** MIT for weights and inference code.
- **Redistributability:** weights and code under MIT with attribution.
- **Recommended strategy:** runtime-fetch of `mlx-community/F5-TTS` (Apple Silicon)
  or `SWivid/F5-TTS` on Linux/CUDA; keep weight blobs out of git and image builds.
- **Operator checklist:** retain MIT notices; install `mlx-audio` on Apple Silicon
  or `f5-tts` on Linux.


## Implementation notes

- CI and open-source builds must pass without downloading gated weights; use
  stub backends or recorded fixtures in tests.
- The short verdict for operators lives in [TTS_LICENSES.md](TTS_LICENSES.md).
