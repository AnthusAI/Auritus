import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { GettysburgExcerpt } from "@/components/GettysburgExcerpt";

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
        <Link href="/examples">Examples</Link>
        <Link href="/examples/basic">Kokoro</Link>
        <Link href="/examples/qwen">Qwen</Link>
      </nav>
      <AuritusPlayerHost
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — themed Kokoro"
      />
      <article className="example-article">
        <GettysburgExcerpt backendLabel="Kokoro (af_heart) and a custom player theme" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — themed Kokoro"
        ttsBackend="kokoro"
        voiceId="af_heart"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
