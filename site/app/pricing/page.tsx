import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { DelegatedResponsibility } from "@/components/DelegatedResponsibility";

export const metadata: Metadata = {
  title: "Pricing — Auritus",
  description:
    "Open-source narration infrastructure with delegated responsibility: run it yourself or let Anthus manage and support your deployment.",
};

export default function PricingPage() {
  return (
    <main>
      <header className="marketing-header">
        <Link
          className="brand-lockup"
          href="/"
          aria-label="Auritus home: Be heard"
        >
          <Image
            className="brand-announcer"
            src="/auritus-announcer.png"
            alt=""
            width={512}
            height={504}
            priority
          />
          <span className="brand-lockup-copy">
            <span className="wordmark">Auritus</span>
            <span className="brand-tagline">
              Be heard<span>.</span>
            </span>
          </span>
        </Link>
        <nav aria-label="Main navigation">
          <div className="nav-links">
            <Link href="/docs/architecture">Architecture</Link>
            <Link href="/docs/security">Security</Link>
            <Link href="/docs">Docs</Link>
            <Link href="/examples">Examples</Link>
            <Link href="/#pricing">Pricing</Link>
          </div>
          <Link className="nav-cta" href="/docs/usage">
            Add to your site
          </Link>
        </nav>
      </header>

      <DelegatedResponsibility />

      <footer className="marketing-footer">
        <Link className="wordmark" href="/">
          Auritus<span>.</span>
        </Link>
        <p>Open-source, just-in-time narration for the web.</p>
        <div>
          <Link href="/#pricing">Pricing</Link>
          <Link href="/docs">Documentation</Link>
          <Link href="/examples">Examples</Link>
          <a href="https://github.com/AnthusAI/Auritus">GitHub</a>
        </div>
      </footer>
    </main>
  );
}
