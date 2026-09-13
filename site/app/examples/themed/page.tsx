import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";

export default function ThemedExamplePage() {
  return (
    <main
      className="page"
      style={
        {
          "--auritus-bg": "#102018",
          "--auritus-fg": "#e8efe9",
          "--auritus-accent": "#3f8f78",
          "--auritus-radius": "12px",
          "--auritus-track": "#294238",
        } as React.CSSProperties
      }
    >
      <nav className="site">
        <Link href="/">Auritus</Link>
        <Link href="/docs">Docs</Link>
        <Link href="/examples/ignore">Ignore example</Link>
      </nav>
      <article className="example-article">
        <h1>Themed player example</h1>
        <p>The player uses custom colors and shape variables.</p>
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Themed player example"
        byline="Design lab"
        root=".example-article"
      />
    </main>
  );
}
