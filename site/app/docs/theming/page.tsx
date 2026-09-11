import Link from "next/link";

export default function ThemingDocsPage() {
  return (
    <main className="page">
      <nav className="site">
        <Link href="/">Auritus</Link>
        <Link href="/docs">Docs</Link>
        <Link href="/examples/themed">Themed example</Link>
      </nav>
      <h1>Theming</h1>
      <p>
        Auritus is designed to inherit the host page. Override with CSS custom
        properties or data attributes on the script tag.
      </p>
      <ul>
        <li>
          <code>--auritus-bg</code>
        </li>
        <li>
          <code>--auritus-fg</code>
        </li>
        <li>
          <code>--auritus-accent</code>
        </li>
        <li>
          <code>--auritus-font</code>
        </li>
        <li>
          <code>--auritus-radius</code>
        </li>
        <li>
          <code>--auritus-track</code>
        </li>
      </ul>
      <pre>{`<script
  src="https://aurit.us/embed.js"
  data-auritus-site-key="..."
  data-auritus-bg="#102018"
  data-auritus-fg="#e8efe9"
  data-auritus-accent="#3f8f78"
  data-auritus-font="Source Sans 3, sans-serif"
></script>`}</pre>
    </main>
  );
}
