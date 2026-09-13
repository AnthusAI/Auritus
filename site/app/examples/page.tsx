import Link from "next/link";

const examples = [
  {
    href: "/examples/basic",
    title: "Basic embed",
    summary: "Kokoro narration of the Gettysburg Address on a sample article.",
  },
  {
    href: "/examples/themed",
    title: "Themed player",
    summary: "Kokoro with CSS variable overrides, reading Pride and Prejudice.",
  },
  {
    href: "/examples/qwen",
    title: "Qwen backend",
    summary:
      "Qwen narration of an Origin of Species excerpt, distinct from Kokoro.",
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
      <p>Acceptance fixtures for the marketing site and behave scenarios.</p>
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
