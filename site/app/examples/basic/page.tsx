import Link from "next/link";
import { AuritusEmbed, AuritusPlayerHost } from "@/components/AuritusEmbed";

export default function BasicExamplePage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/examples">Examples</Link>
        <Link href="/docs/usage">Usage</Link>
      </nav>
      <AuritusPlayerHost />
      <article className="example-article">
        <h1>Basic narration example</h1>
        <p>
          Four score and seven years ago our fathers brought forth on this
          continent, a new nation, conceived in Liberty, and dedicated to the
          proposition that all men are created equal.
        </p>
        <p>
          Now we are engaged in a great civil war, testing whether that nation,
          or any nation so conceived and so dedicated, can long endure. We are
          met on a great battle-field of that war. We have come to dedicate a
          portion of that field, as a final resting place for those who here
          gave their lives that that nation might live. It is altogether fitting
          and proper that we should do this.
        </p>
        <p>
          This page uses the Kokoro TTS backend. The Gettysburg Address is in
          the public domain.
        </p>
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Basic narration example"
        byline="Abraham Lincoln, 1863"
        ttsBackend="kokoro"
        voiceId="af_heart"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
