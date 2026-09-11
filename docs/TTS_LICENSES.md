# TTS model licenses

Auritus itself is MIT-licensed. The TTS backends are separate.

## Higgs (Boson)

- Status: **verify before redistributing weights**
- Strategy: **runtime fetch** of weights (not baked into the Batch image)
- Action: confirm Boson / Higgs license terms and attribution requirements
  before claiming full "open clone" redistributability for model weights.

## Qwen 3

- Status: **verify before redistributing weights**
- Strategy: **runtime fetch** of weights (not baked into the Batch image)
- Action: confirm Alibaba / Qwen license terms (often Apache-2.0 for code,
  with separate terms for weights) before baking or redistributing.

## Decision for v0.1

Ship the pluggable interface and stub generators so the pipeline can be
acceptance-tested. Document weight fetch behind environment variables
(`AURITUS_HIGGS_WEIGHTS_URI`, `AURITUS_QWEN_WEIGHTS_URI`). Do not publish a
Docker image that embeds third-party weights until license sign-off is
recorded here as **approved**.
