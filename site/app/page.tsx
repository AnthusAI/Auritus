import Image from "next/image";
import Link from "next/link";
import { AuritusEmbed } from "@/components/AuritusEmbed";
import { AuritusPlayerHost } from "@/components/AuritusPlayerHost";
import { ElevatorPitch } from "@/components/ElevatorPitch";

const choices = [
  {
    eyebrow: "Your data path",
    title: "Narration on infrastructure you choose.",
    copy: "Keep page text in a stack you operate. Audio stays private by default and is delivered through short-lived access.",
  },
  {
    eyebrow: "Your model",
    title: "Use an open model. Tune the tradeoff.",
    copy: "Choose the voice backend and parameters that fit your quality, latency, and cost targets instead of accepting one fixed service.",
  },
  {
    eyebrow: "Your compute",
    title: "Start local. Fall back when it matters.",
    copy: "A GPU worker you run can claim ordinary work first. AWS Batch is there when that worker is unavailable or the queue needs help.",
  },
];

export default function HomePage() {
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
            <span className="wordmark">
              Auritus<span>.</span>
            </span>
            <span className="brand-tagline">Be heard</span>
          </span>
        </Link>
        <nav aria-label="Main navigation">
          <Link href="/docs/architecture">Architecture</Link>
          <Link href="/docs/security">Security</Link>
          <Link href="/docs">Docs</Link>
          <Link href="/examples">Examples</Link>
          <Link className="nav-cta" href="/docs/usage">
            Add to your site
          </Link>
        </nav>
      </header>

      <section className="marketing-hero" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="kicker">Open source narration infrastructure</p>
          <h1 id="hero-title">Let every article speak.</h1>
          <p className="hero-intro">
            Auritus turns the readable text on any page into on-demand audio —
            with a small embed, open-model workers you run, and an AWS safety
            net behind them.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" href="/docs/usage">
              Start with the embed
            </Link>
            <Link className="text-link" href="/docs/architecture">
              See the architecture <span aria-hidden="true">↓</span>
            </Link>
          </div>
          <dl className="hero-proof">
            <div>
              <dt>Embed</dt>
              <dd>script tag on a publisher page</dd>
            </div>
            <div>
              <dt>Local + cloud</dt>
              <dd>compute paths: local first, cloud fallback</dd>
            </div>
            <div>
              <dt>Open models</dt>
              <dd>models and deployment choices</dd>
            </div>
          </dl>
        </div>
        <div className="hero-visual" aria-label="Auritus request flow diagram">
          <div className="signal-orbit orbit-one" aria-hidden="true" />
          <div className="signal-orbit orbit-two" aria-hidden="true" />
          <Image
            src="/diagrams/overview.svg"
            alt="Auritus turns page content into a job that is handled first by an optional local worker, then by an AWS fallback, before returning private audio to the reader."
            width={2953}
            height={592}
            priority
          />
        </div>
      </section>

      <section className="demo-section" aria-labelledby="demo-title">
        <div className="section-heading compact">
          <p className="kicker">Hear it for yourself</p>
          <h2 id="demo-title">Thirty seconds, in its own voice.</h2>
        </div>
        <div className="demo-panel">
          <AuritusPlayerHost
            name="What Auritus does"
            byline="A 30-second introduction, narrated by Auritus"
          />
          <article className="demo-article">
            <ElevatorPitch />
          </article>
        </div>
        <AuritusEmbed
          siteKey="demo-site-key"
          apiUrl="https://4o6atlkpeh.execute-api.us-east-1.amazonaws.com"
          name="What Auritus does"
          byline="A 30-second introduction, narrated by Auritus"
          ttsBackend="kokoro"
          voiceId="af_heart"
          root=".demo-article"
          playerHost=".demo-panel .auritus-player-host"
        />
      </section>

      <section className="choice-section" aria-labelledby="control-title">
        <div className="section-heading">
          <p className="kicker">Control is the product</p>
          <h2 id="control-title">
            A narration layer that adapts to your stack.
          </h2>
          <p>
            Build a listening experience without treating your publisher content
            and production choices as somebody else&apos;s defaults.
          </p>
        </div>
        <div className="choice-grid">
          {choices.map((choice) => (
            <article className="choice-card" key={choice.title}>
              <p className="card-eyebrow">{choice.eyebrow}</p>
              <h3>{choice.title}</h3>
              <p>{choice.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section
        className="architecture-panel"
        aria-labelledby="architecture-title"
      >
        <div className="architecture-copy">
          <p className="kicker">Designed for a reliable handoff</p>
          <h2 id="architecture-title">
            Your GPU when it is there. AWS when it is not.
          </h2>
          <p>
            A local worker races to claim the job. If nobody claims it during
            the configured window, a workflow submits an AWS Batch GPU job. The
            conditional claim means only one worker finishes the audio.
          </p>
          <ul className="check-list">
            <li>
              Content-hash deduplication keeps repeated requests efficient.
            </li>
            <li>Private audio is returned with short-lived access.</li>
            <li>
              Per-site quotas, budgets, and a kill switch limit cloud work.
            </li>
          </ul>
          <Link className="button button-outline" href="/docs/architecture">
            Explore deployment options
          </Link>
        </div>
        <div className="architecture-diagram">
          <Image
            src="/diagrams/aws-deployment.svg"
            alt="AWS architecture diagram showing the publisher origin, job API, DynamoDB tables, local GPU worker, fallback workflow, AWS Batch, private audio, and signed delivery URL."
            width={2803}
            height={580}
          />
        </div>
      </section>

      <section className="setup-section" aria-labelledby="setup-title">
        <div className="section-heading compact">
          <p className="kicker">A short path to first audio</p>
          <h2 id="setup-title">Deploy, register, embed.</h2>
        </div>
        <ul className="setup-steps">
          <li>
            <div>
              <h3>Deploy your stack</h3>
              <p>
                Provision the API, worker fallback, private audio storage, and
                operator authentication in AWS.
              </p>
            </div>
          </li>
          <li>
            <div>
              <h3>Register an origin</h3>
              <p>
                Create a site key scoped to the publisher domain that will host
                the player.
              </p>
            </div>
          </li>
          <li>
            <div>
              <h3>Drop in the player</h3>
              <p>
                Add the embed once. Auritus extracts the readable content and
                keeps the player in step with your page.
              </p>
            </div>
          </li>
        </ul>
        <Link className="text-link" href="/docs/self-hosting">
          Read the self-hosting guide <span aria-hidden="true">→</span>
        </Link>
      </section>

      <section className="security-note" aria-labelledby="security-title">
        <p className="kicker">Security architecture in progress</p>
        <h2 id="security-title">
          Clear boundaries now. Deeper control evidence next.
        </h2>
        <p>
          Auritus already uses private audio, short-lived delivery, conditional
          job claims, and spend limits. The secure-by-design documentation is
          being developed alongside the implementation, so the architecture page
          distinguishes current behavior from planned controls such as origin
          enforcement and complete JWT validation.
        </p>
        <Link href="/docs/security">
          Read the authentication and security design
        </Link>
      </section>

      <footer className="marketing-footer">
        <Link className="wordmark" href="/">
          Auritus<span>.</span>
        </Link>
        <p>Open-source, just-in-time narration for the web.</p>
        <div>
          <Link href="/docs">Documentation</Link>
          <Link href="/examples">Examples</Link>
          <a href="https://github.com/AnthusAI/Auritus">GitHub</a>
        </div>
      </footer>
    </main>
  );
}
