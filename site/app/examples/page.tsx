import Link from "next/link";

const examples = [
  {
    href: "/examples/basic",
    title: "Kokoro — Gettysburg Address",
    summary:
      "The same two-paragraph Gettysburg excerpt, spoken with Kokoro af_heart.",
  },
  {
    href: "/examples/qwen",
    title: "Qwen — Gettysburg Address",
    summary: "The same Gettysburg excerpt, spoken with Qwen (Ryan).",
  },
  {
    href: "/examples/themed",
    title: "Themed Kokoro player",
    summary: "The same Gettysburg excerpt, Kokoro, with CSS variable chrome.",
  },
  {
    href: "/examples/ignore",
    title: "Ignore markup",
    summary: "Kokoro reading On Liberty while skipping a promotional aside.",
  },
];

export default function ExamplesIndexPage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/">Auritus</Link>
        <Link href="/docs">Docs</Link>
      </nav>
      <h1>Examples</h1>
      <p>
        Kokoro and Qwen are the speech backends. They narrate the same
        Gettysburg excerpt so you can hear the difference. Higgs is a tone stub
        and is not demoed here.
      </p>
      <ul className="doc-index">
        {examples.map((example) => (
          <li key={example.href}>
            <Link href={example.href}>
              <strong>{example.title}</strong>
            </Link>
            <span>{example.summary}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
