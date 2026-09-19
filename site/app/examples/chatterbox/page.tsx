import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function ChatterboxExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="chatterbox" />
      <AuritusPlayerHost
        name="Don't Settle"
        byline="Steve Jobs, 2005 — Chatterbox (Serious)"
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel="Chatterbox — Serious voice (Resemble AI)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline="Steve Jobs, 2005 — Chatterbox (Serious)"
        ttsBackend="chatterbox"
        voiceId="serious"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
