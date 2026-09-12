import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";

export default function IgnoreExamplePage() {
  return (
    <main className="page">
      <nav className="site" data-auritus-ignore>
        <Link href="/examples">Examples</Link>
        <Link href="/docs/ignore-rules">Ignore rules</Link>
      </nav>
      <article className="example-article">
        <h1>Ignore markup example</h1>
        <p>Spoken body text stays in the narration.</p>
        <p data-auritus-ignore>This paragraph is ignored.</p>
        <p data-auritus-pronounce="NASA">NASA</p>
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Ignore markup example"
        byline="Auritus docs"
      />
    </main>
  );
}
