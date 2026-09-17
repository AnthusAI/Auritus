import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function HiggsExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="higgs" />
      <AuritusPlayerHost
        name="Don't Settle"
        byline="Steve Jobs, 2005 — Higgs-v3"
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel="Higgs Audio v3 (Boson AI)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline="Steve Jobs, 2005 — Higgs-v3"
        ttsBackend="higgs"
        voiceId="default"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
