import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { GettysburgExcerpt } from "@/components/GettysburgExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function HiggsExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="higgs" />
      <AuritusPlayerHost
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Higgs-v3"
      />
      <article className="example-article">
        <GettysburgExcerpt backendLabel="Higgs Audio v3 (Boson AI)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Higgs-v3"
        ttsBackend="higgs"
        voiceId="default"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
