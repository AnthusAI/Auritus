import Link from "next/link";

export default function IgnoreRulesDocsPage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/docs">Docs</Link>
        <Link href="/examples/ignore">Ignore example</Link>
      </nav>
      <h1>Ignore rules</h1>
      <p>
        Control what enters the TTS pipeline with CSS selectors on the script tag
        and explicit markup in the article body.
      </p>
      <h2>Script attribute</h2>
      <pre>{`<script
  src="https://aurit.us/embed.js"
  data-auritus-site-key="..."
  data-auritus-ignore=".nav,.ads,.promo"
></script>`}</pre>
      <h2>Inline markup</h2>
      <ul>
        <li>
          <code>data-auritus-ignore</code> — skip an element subtree
        </li>
        <li>
          <code>data-auritus-pronounce=&quot;N A S A&quot;</code> — override
          spoken form
        </li>
        <li>
          <code>data-auritus-break</code> — insert a pause boundary
        </li>
      </ul>
    </main>
  );
}
