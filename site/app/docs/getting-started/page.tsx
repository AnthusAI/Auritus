import Link from 'next/link';
import GettingStartedWizard from '@/components/GettingStartedWizard';

export const metadata = {
  title: 'Getting Started with Auritus',
  description: 'Interactive step-by-step setup guide for Auritus just-in-time web narration infrastructure.',
};

export default function GettingStartedPage() {
  return (
    <main className="documentation-page">
      <nav className="docs-nav" aria-label="Documentation navigation">
        <Link className="wordmark" href="/">
          Auritus<span>.</span>
        </Link>
        <div>
          <Link href="/docs">All docs</Link>
          <Link href="/docs/architecture">Architecture</Link>
          <Link href="/docs/security">Security</Link>
          <Link href="/docs/usage">Usage</Link>
          <Link href="/examples">Examples</Link>
        </div>
      </nav>

      <header className="docs-hero" style={{ marginBottom: '2.5rem' }}>
        <p className="kicker">Interactive Setup Guide</p>
        <h1>Get started with Auritus.</h1>
        <p>
          Configure your narration pipeline from end to end: deploy cloud infrastructure, select your workforce identity provider, test open-source voice models, and generate your custom embed script.
        </p>
      </header>

      <GettingStartedWizard />
    </main>
  );
}
