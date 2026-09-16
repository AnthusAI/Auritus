import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { GettysburgExcerpt } from "@/components/GettysburgExcerpt";
import { ModelCompareNav } from "@/components/ModelCompareNav";

export default function FishExamplePage() {
  return (
    <main className="page">
      <ModelCompareNav currentBackend="fish" />
      <AuritusPlayerHost
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Fish Speech"
      />
      <article className="example-article">
        <GettysburgExcerpt backendLabel="Fish Speech (Fish Audio)" />
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Gettysburg Address"
        byline="Abraham Lincoln, 1863 — Fish Speech"
        ttsBackend="fish"
        voiceId="narrator"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
