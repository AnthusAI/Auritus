import Link from "next/link";

const sections = [
  {
    href: "/docs/architecture",
    title: "Architecture",
    summary: "Visual guide to the local-first worker, AWS fallback, identity choices, and secure-design status.",
  },
  {
    href: "/docs/security",
    title: "Security",
    summary: "Operator authentication, refresh-token rotation, unattended workers, revocation, and notification.",
  },
  {
    href: "/docs/usage",
    title: "Usage",
    summary: "Embed script, site keys, and how jobs flow from browser to audio.",
  },
  {
    href: "/docs/ignore-rules",
    title: "Ignore rules",
    summary: "Selectors and data attributes that shape what gets narrated.",
  },
  {
    href: "/docs/theming",
    title: "Theming",
    summary: "CSS variables and data attributes so the player matches your page.",
  },
  {
    href: "/docs/self-hosting",
    title: "Self-hosting",
    summary: "Deploy the CDK stack, Cognito login, local worker, and guardrails.",
  },
];

export default function DocsPage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/">Auritus</Link>
        <Link href="/examples">Examples</Link>
      </nav>
      <h1>Documentation</h1>
      <p>
        Auritus is a generator plus player: the generator reads the DOM, the
        API keys work by content hash, and audio stays private until your site
        key requests a signed URL.
      </p>
      <ul className="doc-index">
        {sections.map((section) => (
          <li key={section.href}>
            <Link href={section.href}>
              <strong>{section.title}</strong>
            </Link>
            <span>{section.summary}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
