import Link from "next/link";

const modelExamples = [
  {
    href: "/examples/basic",
    title: "Kokoro-82M",
    badge: "82M params",
    creator: "Hexgrad",
    architecture: "StyleTTS 2 + ISTFTNet",
    sampleRate: "24 kHz",
    license: "Apache-2.0",
    summary:
      "The Steve Jobs commencement speech excerpt, spoken with Kokoro-82M on Apple Silicon (MLX) or PyTorch.",
  },
  {
    href: "/examples/qwen",
    title: "Qwen3-TTS",
    badge: "0.6B params",
    creator: "Alibaba Qwen",
    architecture: "CustomVoice 12Hz Transformer",
    sampleRate: "24 kHz",
    license: "Apache-2.0",
    summary:
      "The same commencement speech excerpt, spoken with Qwen3-TTS 0.6B CustomVoice with the Ryan preset.",
  },
  {
    href: "/examples/f5",
    title: "F5-TTS",
    badge: "Flow matching",
    creator: "SWivid",
    architecture: "Non-autoregressive Flow Matching",
    sampleRate: "24 kHz",
    license: "MIT",
    summary:
      "The same commencement speech excerpt, spoken with non-autoregressive F5-TTS via MLX on Apple Silicon.",
  },
  {
    href: "/examples/higgs",
    title: "Higgs Audio v3",
    badge: "Boson AI 4B",
    creator: "Boson AI",
    architecture: "Higgs Audio 4B Transformer",
    sampleRate: "24 kHz",
    license: "Research / Non-Commercial",
    summary:
      "The same commencement speech excerpt, spoken with Boson AI's expressive 4B Higgs Audio v3 via MLX on Apple Silicon.",
  },
  {
    href: "/examples/chatterbox",
    title: "Chatterbox-TTS",
    badge: "520M Hybrid",
    creator: "Resemble AI",
    architecture: "LLaMA-520M + Matcha-TTS Flow",
    sampleRate: "24 kHz",
    license: "Apache-2.0",
    summary:
      "The same commencement speech excerpt, spoken with Resemble AI's hybrid LLaMA-520M and Matcha-TTS flow matching.",
  },
  {
    href: "/examples/fish",
    title: "Fish-Speech",
    badge: "Dual-AR",
    creator: "Fish Audio",
    architecture: "Dual-AR Transformer + VQ-GAN",
    sampleRate: "44.1 kHz",
    license: "CC-BY-NC-SA-4.0",
    summary:
      "The same commencement speech excerpt, spoken with Fish Audio's dual-autoregressive model with natural prosody and breathing.",
  },
];

const featureExamples = [
  {
    href: "/examples/themed",
    title: "Themed Player",
    badge: "CSS variables",
    summary:
      "The same commencement speech excerpt with Kokoro, styled via CSS custom properties (--auritus-*).",
  },
  {
    href: "/examples/ignore",
    title: "Ignore & Pronounce Markup",
    badge: "Article parsing",
    summary:
      "John Stuart Mill's On Liberty demonstrating data-auritus-ignore to skip ads and data-auritus-pronounce.",
  },
];

export default function ExamplesIndexPage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/">Auritus</Link>
        <Link href="/docs">Docs</Link>
        <Link href="/docs/usage">Usage</Link>
      </nav>
      <h1>Examples &amp; Models</h1>
      <p>
        Kokoro, Qwen, F5, Higgs, Chatterbox, and Fish Speech are the supported speech backends.
        Each model narrates the identical excerpt from Steve Jobs&#39;s Stanford Commencement Address so you
        can directly compare audio timbre, pacing, pronunciation, and latency.
      </p>

      <section style={{ marginTop: "2.5rem" }}>
        <h2 style={{ fontSize: "1.4rem", marginBottom: "0.5rem" }}>
          Speech Model Comparison
        </h2>
        <p style={{ color: "var(--ink-muted)", fontSize: "0.95rem" }}>
          Compare five open model architectures running on Apple Silicon (MLX) and AWS Batch:
        </p>

        <div className="model-cards-grid" style={{ marginTop: "1.25rem" }}>
          {modelExamples.map((example) => (
            <article key={example.href} className="model-showcase-card">
              <div className="model-card-header">
                <div>
                  <h3 className="model-card-title">{example.title}</h3>
                  <span className="model-card-creator">by {example.creator}</span>
                </div>
                <span className="badge-pill">{example.badge}</span>
              </div>
              <p className="model-card-summary">{example.summary}</p>
              <div className="model-card-meta">
                <span>{example.architecture}</span>
                <span>•</span>
                <span>{example.sampleRate}</span>
                <span>•</span>
                <span>{example.license}</span>
              </div>
              <div className="model-card-actions">
                <Link href={example.href} className="button button-primary">
                  Listen &amp; Compare →
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section style={{ marginTop: "3.5rem" }}>
        <h2 style={{ fontSize: "1.4rem", marginBottom: "0.5rem" }}>
          Embed Features &amp; Theming
        </h2>
        <p style={{ color: "var(--ink-muted)", fontSize: "0.95rem" }}>
          Customizing player appearance and article content extraction:
        </p>
        <ul className="doc-index" style={{ marginTop: "1rem" }}>
          {featureExamples.map((example) => (
            <li key={example.href}>
              <Link
                href={example.href}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.6rem",
                }}
              >
                <strong>{example.title}</strong>
                <span className="badge-pill">{example.badge}</span>
              </Link>
              <span>{example.summary}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
