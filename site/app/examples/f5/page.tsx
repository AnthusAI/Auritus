import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function F5ExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="f5" />
      <AuritusPlayerHost
        name="Don't Settle"
        byline="Steve Jobs, 2005 — F5-TTS (Serious)"
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel="F5-TTS — Serious voice (Flow-matching)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Don't Settle"
        byline="Steve Jobs, 2005 — F5-TTS (Serious)"
        ttsBackend="f5"
        voiceId="serious"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
