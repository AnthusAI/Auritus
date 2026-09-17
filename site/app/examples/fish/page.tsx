import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { JobsCommencementExcerpt } from "@/components/JobsCommencementExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function FishExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="fish" />
      <AuritusPlayerHost
        name="Stanford Commencement Address"
        byline="Steve Jobs, 2005 — Fish Speech"
      />
      <article className="example-article">
        <JobsCommencementExcerpt backendLabel="Fish Speech (Fish Audio)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Stanford Commencement Address"
        byline="Steve Jobs, 2005 — Fish Speech"
        ttsBackend="fish"
        voiceId="narrator"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
