# TTS model licenses

Auritus itself is MIT-licensed. The TTS backends are separate. This is not
legal advice. Operators must confirm the cited cards before redistributing
weights.

Recorded 13 September 2026 against the backends Auritus actually ships.

## Kokoro (default speech)

- Checkpoint: [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
- Weights license: **Apache-2.0** (Hugging Face `license: apache-2.0`)
- Inference package: `kokoro` on PyPI (worker image pins `kokoro==0.9.4`)
- Image policy: pip wheels may be baked; **model weights are fetched at
  runtime**, not copied into the git tree or the Docker build context
- Extra dependency: typical Kokoro pipelines use **espeak-ng (GPLv3)** for
  grapheme-to-phoneme. Redistributing a binary that links espeak-ng can carry
  GPL obligations even though the weights are Apache-2.0.

## Qwen 3 CustomVoice

- Checkpoint: [Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice)
- Code: [QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) and PyPI
  `qwen-tts==0.1.1` (**Apache-2.0**)
- Weights license: **Apache-2.0** on the CustomVoice model card
- Image policy: `qwen-tts` and `torchaudio` wheels may be baked; **weights are
  fetched at runtime** (Hugging Face cache on the worker)

## Higgs (Boson)

- Checkpoint: [bosonai/higgs-audio-v3-tts-4b](https://huggingface.co/bosonai/higgs-audio-v3-tts-4b) and [multimodalart/higgs-audio-v3-tts-4b-transformers](https://huggingface.co/multimodalart/higgs-audio-v3-tts-4b-transformers)
- Code: `mlx-audio` on Apple Silicon (`higgs_audio_v3`), `transformers` / PyTorch on Linux/CUDA
- Weights license: **Boson Higgs TTS 3 Research and Non-Commercial License Agreement** (Hugging Face model card)
- Image policy: `mlx-audio` and `transformers` wheels installed; **model weights are fetched at runtime**, not copied into the git tree or Docker build context
- Usage restriction: Research and non-commercial use only. Operators deploying commercially must secure commercial licensing from Boson AI.

## F5-TTS (MLX on Apple Silicon)

- Checkpoint: [SWivid/F5-TTS](https://huggingface.co/SWivid/F5-TTS) and [mlx-community/F5-TTS](https://huggingface.co/mlx-community/F5-TTS)
- Code: [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS) (**MIT**)
- Weights license: **MIT**
- Platform policy: `mlx-audio` native on Apple Silicon; `f5-tts` fallback on
  NVIDIA/CPU. Model weights fetched at runtime.


## Decision for the current ship

- Public examples and Batch jobs support **Kokoro**, **Qwen**, **F5**, and **Higgs**.
- The Batch image may install open pip packages. It must not COPY large
  third-party weight blobs from the repository.
- PyPI publish of the Auritus CLI remains a separate story (`a01473`) and is
  not enabled until `AURITUS_PUBLISH_PYPI` is set.

See [MODEL_LICENSES.md](MODEL_LICENSES.md) for the tabular checklist.
