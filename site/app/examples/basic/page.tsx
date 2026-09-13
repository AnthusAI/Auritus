import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { GettysburgExcerpt } from "@/components/GettysburgExcerpt";

export default function BasicExamplePage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/examples">Examples</Link>
        <Link href="/examples/qwen">Same excerpt in Qwen</Link>
        <Link href="/docs/usage">Usage</Link>
      </nav>
      <AuritusPlayerHost
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Kokoro"
      />
      <article className="example-article">
        <GettysburgExcerpt backendLabel="Kokoro (af_heart)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Kokoro"
        ttsBackend="kokoro"
        voiceId="af_heart"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
