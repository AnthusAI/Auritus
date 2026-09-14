import Link from "next/link";

const modelExamples = [
  {
    href: "/examples/basic",
    title: "Kokoro-82M — Gettysburg Address",
    badge: "af_heart voice",
    summary:
      "The two-paragraph Gettysburg excerpt, spoken with Kokoro-82M on Apple Silicon (MLX) or PyTorch (~23s).",
  },
  {
    href: "/examples/qwen",
    title: "Qwen3-TTS — Gettysburg Address",
    badge: "Ryan voice",
    summary:
      "The same Gettysburg excerpt, spoken with Qwen3-TTS 0.6B CustomVoice (~48s).",
  },
  {
    href: "/examples/f5",
    title: "F5-TTS — Gettysburg Address",
    badge: "Flow matching",
    summary:
      "The same Gettysburg excerpt, spoken with non-autoregressive F5-TTS via MLX on Apple Silicon.",
  },
];

const featureExamples = [
  {
    href: "/examples/themed",
    title: "Themed Player",
    badge: "CSS variables",
    summary:
      "The same Gettysburg excerpt with Kokoro, styled via CSS custom properties (--auritus-*).",
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
      <h1>Examples</h1>
      <p>
        Kokoro, Qwen, and F5 are the speech backends. They narrate the identical
        two-paragraph Gettysburg excerpt so you can directly compare audio
        timbre, pacing, and quality.
      </p>

      <section style={{ marginTop: "2.5rem" }}>
        <h2 style={{ fontSize: "1.4rem", marginBottom: "0.5rem" }}>
          Model Comparison
        </h2>
        <p style={{ color: "var(--ink-muted)", fontSize: "0.95rem" }}>
          The same excerpt spoken by three open model architectures:
        </p>
        <ul className="doc-index" style={{ marginTop: "1rem" }}>
          {modelExamples.map((example) => (
            <li key={example.href}>
              <Link href={example.href}>
                <strong>{example.title}</strong>
              </Link>
              <span>{example.summary}</span>
            </li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: "3rem" }}>
        <h2 style={{ fontSize: "1.4rem", marginBottom: "0.5rem" }}>
          Embed Features &amp; Theming
        </h2>
        <p style={{ color: "var(--ink-muted)", fontSize: "0.95rem" }}>
          Customizing player appearance and article content extraction:
        </p>
        <ul className="doc-index" style={{ marginTop: "1rem" }}>
          {featureExamples.map((example) => (
            <li key={example.href}>
              <Link href={example.href}>
                <strong>{example.title}</strong>
              </Link>
              <span>{example.summary}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}

