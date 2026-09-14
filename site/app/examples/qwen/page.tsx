import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { GettysburgExcerpt } from "@/components/GettysburgExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function QwenExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="qwen" />
      <AuritusPlayerHost
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Qwen"
      />
      <article className="example-article">
        <GettysburgExcerpt backendLabel="Qwen (Ryan)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Qwen"
        ttsBackend="qwen"
        voiceId="Ryan"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
