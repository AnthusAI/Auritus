import Link from "next/link";

export default function SelfHostingDocsPage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/">Auritus</Link>
        <Link href="/docs">Docs</Link>
      </nav>
      <h1>Self-hosting</h1>
      <ol>
        <li>
          Deploy the CDK stack: <code>auritus deploy</code>
        </li>
        <li>
          Put your Google OAuth client id/secret into the stack&apos;s Secrets
          Manager secret, then attach Google as a Cognito IdP.
        </li>
        <li>
          <code>auritus login</code> (Cognito Google OAuth, short-lived JWTs)
        </li>
        <li>
          <code>auritus site create --origin https://your.site</code>
        </li>
        <li>
          Run <code>auritus worker</code> on hardware you control so it wins the
          race against the 15-minute Batch fallback.
        </li>
      </ol>
      <p>
        Spend guardrails: AWS Budgets disables the Batch queue at the daily
        threshold; per-site quotas apply; <code>auritus killswitch disable</code>{" "}
        is the manual stop.
      </p>
    </main>
  );
}
