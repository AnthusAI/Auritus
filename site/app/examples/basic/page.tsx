import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { GettysburgExcerpt } from "@/components/GettysburgExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function BasicExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="kokoro" />
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
