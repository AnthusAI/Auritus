# TTS model licenses (research notes)

This document tracks license posture for the first Auritus TTS backends. It is
not legal advice. Confirm each row with counsel before redistributing weights or
shipping a public worker image.

**Provisional weight strategy (all backends):** fetch model weights at runtime
from an operator-controlled bucket or Hugging Face cache on the worker host.
Do not bake proprietary or unclearly licensed weights into public container
images or the open-source repository.

| Backend | Vendor / model | License (provisional) | Redistributable weights? | Image-baked weights | Runtime-fetch weights | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| Higgs | Boson Higgs TTS (exact checkpoint TBD) | NEEDS_HUMAN_VERIFY (likely custom / research terms on Boson assets) | NEEDS_HUMAN_VERIFY | Not recommended for public images | **Recommended** | NEEDS_HUMAN_VERIFY |
| Qwen 3 | Qwen3-TTS family (Alibaba Cloud) | NEEDS_HUMAN_VERIFY (typically Qwen / Tongyi license on model card) | NEEDS_HUMAN_VERIFY | Not recommended until license is confirmed | **Recommended** | NEEDS_HUMAN_VERIFY |

## Higgs (Boson)

- **License name:** NEEDS_HUMAN_VERIFY — read the Boson model card and any
  separate Boson AI terms for the exact Higgs checkpoint Auritus will pin.
- **Redistributability:** NEEDS_HUMAN_VERIFY. Assume weights are **not**
  redistributable in Docker Hub / public ECR until counsel signs off.
- **Recommended strategy:** runtime-fetch from a private S3 prefix or HF token
  scoped to the operator account; pin version by content hash in worker config.
- **Operator checklist:** record license URL, permitted use (commercial vs
  research), attribution requirements, and whether fine-tuned voices may be
  exported.

## Qwen 3

- **License name:** NEEDS_HUMAN_VERIFY — confirm on the pinned Hugging Face
  model card (Qwen Team license text varies by checkpoint).
- **Redistributability:** NEEDS_HUMAN_VERIFY. Many Qwen checkpoints allow use
  under stated terms but restrict redistribution of weights; verify for the
  exact TTS checkpoint.
- **Recommended strategy:** runtime-fetch with `HF_TOKEN` or private mirror; keep
  weights out of the open `worker-image/` build context.
- **Operator checklist:** note whether output audio has additional use
  restrictions; store the license snapshot in internal compliance records.

## Implementation notes

- Worker containers should support `AURITUS_WEIGHTS_URI` (or equivalent) per
  backend so Batch and local workers share the same fetch path.
- CI and open-source builds must pass without downloading gated weights; use
  stub backends or recorded fixtures in tests.
- When verification completes, replace NEEDS_HUMAN_VERIFY cells with citations
  (URL + date) and update the Kanbus compliance task.
