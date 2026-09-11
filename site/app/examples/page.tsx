import Link from "next/link";

const examples = [
  {
    href: "/examples/basic",
    title: "Basic embed",
    summary: "Script tag with site key, title, and byline on a sample article.",
  },
  {
    href: "/examples/themed",
    title: "Themed player",
    summary: "CSS variable overrides for background, type, and accent.",
  },
  {
    href: "/examples/ignore",
    title: "Ignore markup",
    summary: "Promo aside and inline ignore/pronounce attributes.",
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
