import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function F5ExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="f5" />
      <AuritusPlayerHost
        name="Stanford Commencement Address"
        byline="Steve Jobs, 2005 — F5-TTS"
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel="F5-TTS (Flow-matching)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Stanford Commencement Address"
        byline="Steve Jobs, 2005 — F5-TTS"
        ttsBackend="f5"
        voiceId="default"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
