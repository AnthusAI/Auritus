import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";

export default function ThemedExamplePage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/">Auritus</Link>
        <Link href="/docs">Docs</Link>
        <Link href="/examples/ignore">Ignore example</Link>
      </nav>
      <article className="example-article">
        <h1>Themed player example</h1>
        <p>
          The player on this page uses custom colors and font to match a darker
          host aesthetic.
        </p>
      </article>
      <AuritusEmbed
        name="Themed player example"
        byline="Design lab"
        bg="#102018"
        fg="#e8efe9"
        accent="#3f8f78"
        font="Source Sans 3, Helvetica Neue, sans-serif"
      />
    </main>
  );
}
