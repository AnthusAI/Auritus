import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <p className="eyebrow">Open source · MIT</p>
        <h1 className="brand">Auritus</h1>
        <p>
          Just-in-time narration for the open web. One script tag extracts what
          readers should hear, races your local GPU worker against a cloud
          fallback, and plays audio through a player that respects your type and
          color.
        </p>
        <div className="cta">
          <Link className="button" href="/docs">
            Get started
          </Link>
        </div>
      </section>
      <nav className="site">
        <Link href="/docs">Docs</Link>
        <Link href="/examples">Examples</Link>
        <Link href="/docs/self-hosting">Self-hosting</Link>
      </nav>
    </>
  );
}
