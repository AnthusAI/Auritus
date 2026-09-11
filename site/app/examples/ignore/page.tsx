import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";

export default function IgnoreExamplePage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/examples">Examples</Link>
        <Link href="/docs/ignore-rules">Ignore rules</Link>
      </nav>
      <article className="example-article">
        <h1>Ignore markup example</h1>
        <aside className="promo">This promo must not be narrated.</aside>
        <p>
          Spoken body text stays.{" "}
          <span data-auritus-ignore>This span is ignored.</span>
        </p>
        <p data-auritus-pronounce="NASA">NASA</p>
      </article>
      <AuritusEmbed
        name="Ignore markup example"
        byline="Auritus docs"
        ignore=".promo"
      />
    </main>
  );
}
