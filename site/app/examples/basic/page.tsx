import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function BasicExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="kokoro" />
      <AuritusPlayerHost
        name="Don't Settle"
        byline="Steve Jobs, 2005 — Kokoro"
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel="Kokoro (af_heart)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline="Steve Jobs, 2005 — Kokoro"
        ttsBackend="kokoro"
        voiceId="af_heart"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
