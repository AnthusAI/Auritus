import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";

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
        name="Stanford Commencement Address"
        byline="Steve Jobs, 2005 — themed Kokoro"
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel="Kokoro (af_heart) and a custom player theme" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Stanford Commencement Address"
        byline="Steve Jobs, 2005 — themed Kokoro"
        ttsBackend="kokoro"
        voiceId="af_heart"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
