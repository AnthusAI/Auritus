import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";

export default function IgnoreExamplePage() {
  return (
    <main className="page">
      <nav className="site" data-auritus-ignore>
        <Link href="/examples">Examples</Link>
        <Link href="/examples/basic">Basic example</Link>
        <Link href="/docs/ignore-rules">Ignore rules</Link>
      </nav>
      <div className="auritus-player-host" />
      <article className="example-article">
        <h1>Ignore markup example</h1>
        <p>
          The only freedom which deserves the name, is that of pursuing our own
          good in our own way, so long as we do not attempt to deprive others of
          theirs, or impede their efforts to obtain it. Each is the proper
          guardian of his own health, whether bodily, or mental and spiritual.
        </p>
        <p>
          Mankind are greater gainers by suffering each other to live as seems
          good to themselves, than by compelling each to live as seems good to
          the rest.
        </p>
        <p data-auritus-ignore>
          This paragraph is ignored. It is a promotional aside and must not
          appear in the narration.
        </p>
        <p data-auritus-pronounce="NASA">NASA</p>
        <p>
          This page uses Kokoro. The spoken paragraphs are from On Liberty,
          which is in the public domain.
        </p>
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Ignore markup example"
        byline="John Stuart Mill, 1859"
        ttsBackend="kokoro"
        voiceId="af_heart"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
