import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { GettysburgExcerpt } from "@/components/GettysburgExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function ChatterboxExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="chatterbox" />
      <AuritusPlayerHost
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Chatterbox"
      />
      <article className="example-article">
        <GettysburgExcerpt backendLabel="Chatterbox (Resemble AI)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Chatterbox"
        ttsBackend="chatterbox"
        voiceId="narrator"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
