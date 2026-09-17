import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function ChatterboxExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="chatterbox" />
      <AuritusPlayerHost
        name="Stanford Commencement Address"
        byline="Steve Jobs, 2005 — Chatterbox"
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel="Chatterbox (Resemble AI)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Stanford Commencement Address"
        byline="Steve Jobs, 2005 — Chatterbox"
        ttsBackend="chatterbox"
        voiceId="narrator"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
