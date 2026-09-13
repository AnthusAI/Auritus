import Link from "next/link";

export default function UsageDocsPage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/docs">Docs</Link>
        <Link href="/examples/basic">Basic example</Link>
      </nav>
      <h1>Usage</h1>
      <p>
        Add the embed script to pages you want narrated. The generator posts
        normalized text to the Auritus API with your site key; the player polls
        job status and plays audio when it is ready.
      </p>
      <h2>Embed</h2>
      <pre>{`<script
  src="https://aurit.us/embed.js"
  data-auritus-site-key="YOUR_SITE_KEY"
  data-auritus-name="Article title"
  data-auritus-byline="By Author"
></script>`}</pre>
      <p>
        Create site keys with the CLI after{" "}
        <code>auritus login --username</code>. Each key
        is scoped to allowed origins and daily quotas on the router Lambda.
      </p>
      <h2>Content hash</h2>
      <p>
        Hash = normalize(text) + voice_id + tts_backend. Title and byline are
        cosmetic and do not change the hash.
      </p>
      <h2>Workers</h2>
      <p>
        Run <code>auritus worker</code> on hardware you control so local GPU
        claims win the mutex before the Batch fallback timer fires.
      </p>
    </main>
  );
}
