import Link from "next/link";

interface ModelCompareNavProps {
  currentBackend: "kokoro" | "qwen" | "f5";
}

const models = [
  { id: "kokoro", label: "Kokoro-82M", href: "/examples/basic" },
  { id: "qwen", label: "Qwen3-TTS", href: "/examples/qwen" },
  { id: "f5", label: "F5-TTS", href: "/examples/f5" },
] as const;

export function ModelCompareNav({ currentBackend }: ModelCompareNavProps) {
  return (
    <nav className="site" aria-label="Model comparison navigation">
      <Link href="/examples">← Examples</Link>
      <span aria-hidden="true" style={{ opacity: 0.35 }}>
        |
      </span>
      <span style={{ fontWeight: 600 }}>Compare Models:</span>
      {models.map((model) =>
        model.id === currentBackend ? (
          <span
            key={model.id}
            style={{
              fontWeight: 700,
              color: "var(--accent)",
              borderBottom: "2px solid var(--accent)",
            }}
          >
            {model.label}
          </span>
        ) : (
          <Link key={model.id} href={model.href}>
            {model.label}
          </Link>
        )
      )}
      <span aria-hidden="true" style={{ opacity: 0.35 }}>
        |
      </span>
      <Link href="/docs/usage">Usage</Link>
    </nav>
  );
}
