import Link from "next/link";
import Script from "next/script";

export default function BasicExamplePage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/examples">Examples</Link>
        <Link href="/docs/usage">Usage</Link>
      </nav>
      <article className="example-article">
        <h1>Basic narration example</h1>
        <p>
          This page loads the embed the same way a production article would: a
          single async script with data attributes for the site key and display
          metadata.
        </p>
        <p>
          When a local worker is running, narration should complete without
          waiting for the cloud Batch fallback.
        </p>
      </article>
      <pre className="snippet">{`<script
  src="https://aurit.us/embed.js"
  async
  data-auritus-site-key="demo-site-key"
  data-auritus-name="Basic narration example"
  data-auritus-byline="Auritus docs"
></script>`}</pre>
      <Script
        src="/embed.js"
        strategy="afterInteractive"
        data-auritus-site-key="demo-site-key"
        data-auritus-name="Basic narration example"
        data-auritus-byline="Auritus docs"
      />
    </main>
  );
}
