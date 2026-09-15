"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

export type TTSModelId = "kokoro" | "qwen" | "f5" | "higgs" | "chatterbox";

export interface ModelInfo {
  id: TTSModelId;
  name: string;
  badge: string;
  href: string;
  creator: string;
  architecture: string;
  sampleRate: string;
  license: string;
  latencyNote: string;
}

export const TTS_MODELS: readonly ModelInfo[] = [
  {
    id: "kokoro",
    name: "Kokoro-82M",
    badge: "82M",
    href: "/examples/basic",
    creator: "Hexgrad",
    architecture: "StyleTTS 2 + ISTFTNet",
    sampleRate: "24 kHz",
    license: "Apache-2.0",
    latencyNote: "~23s audio on Apple Silicon MLX",
  },
  {
    id: "qwen",
    name: "Qwen3-TTS",
    badge: "0.6B",
    href: "/examples/qwen",
    creator: "Alibaba Qwen",
    architecture: "CustomVoice 12Hz Transformer",
    sampleRate: "24 kHz",
    license: "Apache-2.0",
    latencyNote: "~48s audio on Apple Silicon MLX",
  },
  {
    id: "f5",
    name: "F5-TTS",
    badge: "Flow",
    href: "/examples/f5",
    creator: "SWivid",
    architecture: "Non-autoregressive Flow Matching",
    sampleRate: "24 kHz",
    license: "MIT",
    latencyNote: "Diffusion flow matching via MLX",
  },
  {
    id: "higgs",
    name: "Higgs-v3",
    badge: "4B",
    href: "/examples/higgs",
    creator: "Boson AI",
    architecture: "Higgs Audio 4B Transformer",
    sampleRate: "24 kHz",
    license: "Research / Non-Commercial",
    latencyNote: "Expressive conversational narration",
  },
  {
    id: "chatterbox",
    name: "Chatterbox",
    badge: "520M",
    href: "/examples/chatterbox",
    creator: "Resemble AI",
    architecture: "LLaMA-520M + Matcha-TTS Flow",
    sampleRate: "24 kHz",
    license: "Apache-2.0",
    latencyNote: "Hybrid autoregressive + flow matching",
  },
] as const;

interface ModelCompareNavProps {
  currentBackend: TTSModelId;
}

export function ModelCompareNav({ currentBackend }: ModelCompareNavProps) {
  const router = useRouter();

  const currentIndex = TTS_MODELS.findIndex((m) => m.id === currentBackend);
  const currentModel =
    currentIndex !== -1 ? TTS_MODELS[currentIndex] : TTS_MODELS[0];
  const prevModel =
    currentIndex > 0
      ? TTS_MODELS[currentIndex - 1]
      : TTS_MODELS[TTS_MODELS.length - 1];
  const nextModel =
    currentIndex < TTS_MODELS.length - 1
      ? TTS_MODELS[currentIndex + 1]
      : TTS_MODELS[0];

  return (
    <nav className="model-compare-shell" aria-label="Model comparison navigation">
      <div className="model-compare-topbar">
        <Link href="/examples" className="model-nav-back">
          ← All Examples
        </Link>

        <div className="model-nav-stepper">
          <Link
            href={prevModel.href}
            className="model-stepper-btn"
            title={`Previous: ${prevModel.name}`}
            aria-label={`Previous model: ${prevModel.name}`}
          >
            ‹ {prevModel.name}
          </Link>
          <span className="model-stepper-indicator">
            {currentIndex + 1} of {TTS_MODELS.length}
          </span>
          <Link
            href={nextModel.href}
            className="model-stepper-btn"
            title={`Next: ${nextModel.name}`}
            aria-label={`Next model: ${nextModel.name}`}
          >
            {nextModel.name} ›
          </Link>
        </div>

        <Link href="/docs/usage" className="model-nav-docs">
          Usage →
        </Link>
      </div>

      <div className="model-switcher-bar">
        <div className="model-pills-container" role="tablist" aria-label="TTS Models">
          {TTS_MODELS.map((model) => {
            const isActive = model.id === currentBackend;
            return (
              <Link
                key={model.id}
                href={model.href}
                role="tab"
                aria-selected={isActive}
                className={`model-pill ${isActive ? "active" : ""}`}
              >
                <span className="model-pill-name">{model.name}</span>
                <span className="model-pill-badge">{model.badge}</span>
              </Link>
            );
          })}
        </div>

        <div className="model-select-wrapper">
          <label htmlFor="model-select-dropdown" className="sr-only">
            Select TTS Model
          </label>
          <select
            id="model-select-dropdown"
            className="model-select-dropdown"
            value={currentModel.href}
            onChange={(e) => router.push(e.target.value)}
          >
            {TTS_MODELS.map((model) => (
              <option key={model.id} value={model.href}>
                {model.name} ({model.badge}) — {model.creator}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="model-spec-strip" aria-label="Current model specifications">
        <div className="model-spec-item">
          <span className="spec-label">Architecture</span>
          <strong className="spec-value">{currentModel.architecture}</strong>
        </div>
        <div className="model-spec-item">
          <span className="spec-label">Creator</span>
          <span className="spec-value">{currentModel.creator}</span>
        </div>
        <div className="model-spec-item">
          <span className="spec-label">Sampling</span>
          <span className="spec-value">{currentModel.sampleRate} Mono</span>
        </div>
        <div className="model-spec-item">
          <span className="spec-label">License</span>
          <span className="spec-value">{currentModel.license}</span>
        </div>
      </div>
    </nav>
  );
}
