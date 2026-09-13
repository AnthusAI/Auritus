import Link from "next/link";
import { AuritusEmbed, AuritusPlayerHost } from "@/components/AuritusEmbed";

export default function QwenExamplePage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/examples">Examples</Link>
        <Link href="/docs/usage">Usage</Link>
      </nav>
      <AuritusPlayerHost />
      <article className="example-article">
        <h1>Qwen narration example</h1>
        <p>
          When on board H.M.S. Beagle, as naturalist, I was much struck with
          certain facts in the distribution of the inhabitants of South America,
          and in the geological relations of the present to the past inhabitants
          of that continent. These facts seemed to me to throw some light on the
          origin of species, that mystery of mysteries, as it has been called by
          one of our greatest philosophers.
        </p>
        <p>
          On my return home, it occurred to me, in 1837, that something might
          perhaps be made out on this question by patiently accumulating and
          reflecting on all sorts of facts which could possibly have any bearing
          on it. After five years work I allowed myself to speculate on the
          subject, and drew up some short notes; these I enlarged in 1844 into a
          sketch of the conclusions, which then seemed to me probable: from that
          period to the present day I have steadily pursued the same object.
        </p>
        <p>
          This page uses the Qwen TTS backend. The excerpt is from On the Origin
          of Species, which is in the public domain.
        </p>
      </article>
      <AuritusEmbed
        siteKey="demo-site-key"
        apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
        name="Qwen narration example"
        byline="Charles Darwin, 1859"
        ttsBackend="qwen"
        voiceId="Ryan"
        root=".example-article"
        playerHost=".auritus-player-host"
      />
    </main>
  );
}
