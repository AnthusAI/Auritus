import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function QwenExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="qwen" />
      <AuritusPlayerHost
        name="Don't Settle"
        byline="Steve Jobs, 2005 — Qwen"
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel="Qwen (Ryan)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline="Steve Jobs, 2005 — Qwen"
        ttsBackend="qwen"
        voiceId="Ryan"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
