import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";

export default function BasicExamplePage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/examples">Examples</Link>
        <Link href="/docs/usage">Usage</Link>
      </nav>
      <article className="example-article">
        <h1>Basic narration example</h1>
        <p>This page demonstrates the default Auritus player.</p>
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Basic narration example"
        byline="Auritus docs"
      />
    </main>
  );
}
