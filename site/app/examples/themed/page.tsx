import Link from "next/link";
import { AuritusEmbed, AuritusPlayerHost } from "@/components/AuritusEmbed";

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
      <AuritusPlayerHost />
      <article className="example-article">
        <h1>Themed player example</h1>
        <p>
          It is a truth universally acknowledged, that a single man in
          possession of a good fortune, must be in want of a wife.
        </p>
        <p>
          However little known the feelings or views of such a man may be on his
          first entering a neighbourhood, this truth is so well fixed in the
          minds of the surrounding families, that he is considered the rightful
          property of some one or other of their daughters.
        </p>
        <p>
          This page uses Kokoro with a custom player theme. The excerpt is from
          Pride and Prejudice, which is in the public domain.
        </p>
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Themed player example"
        byline="Jane Austen, 1813"
        ttsBackend="kokoro"
        voiceId="af_heart"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
