import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { GettysburgExcerpt } from "@/components/GettysburgExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function F5ExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="f5" />
      <AuritusPlayerHost
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — F5-TTS"
      />
      <article className="example-article">
        <GettysburgExcerpt backendLabel="F5-TTS (Flow-matching)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — F5-TTS"
        ttsBackend="f5"
        voiceId="default"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
