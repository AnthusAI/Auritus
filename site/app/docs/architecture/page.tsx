import Image from "next/image";
import Link from "next/link";

const identityOptions = [
  {
    title: "Native Cognito users",
    status: "Supported now",
    description:
      "The operator CLI signs in with a Cognito email and password and uses short-lived JWTs for operator routes.",
  },
  {
    title: "Google project through Cognito",
    status: "Configuration required",
    description:
      "The stack has an optional Google IdP resource, but a real Google client and Cognito user-pool domain still need to be configured and tested. The current CLI does not use this path.",
  },
  {
    title: "AWS IAM Identity Center",
    status: "Future enterprise option",
    description:
      "IAM Identity Center can provide a SAML 2.0 application path through Cognito, but Auritus has not implemented or reviewed it yet.",
  },
];

export default function ArchitecturePage() {
  return (
    <main className="documentation-page">
      <nav className="docs-nav" aria-label="Documentation navigation">
        <Link className="wordmark" href="/">
          Auritus<span>.</span>
        </Link>
        <div>
          <Link href="/docs">All docs</Link>
          <Link href="/docs/self-hosting">Self-hosting</Link>
        </div>
      </nav>

      <header className="docs-hero">
        <p className="kicker">Architecture</p>
        <h1>Control the voice, the compute, and the path your content takes.</h1>
        <p>
          Auritus is a local-first, AWS-backed narration pipeline. It gives a
          publisher one embed while leaving deployment and model decisions with
          the team that operates it.
        </p>
      </header>

      <section className="docs-diagram" aria-labelledby="overview-heading">
        <div className="docs-section-title">
          <p className="kicker">High-level flow</p>
          <h2 id="overview-heading">From a readable page to private playback.</h2>
        </div>
        <Image
          src="/diagrams/overview.svg"
          alt="Auritus overview: the publisher page extracts text, requests audio, sends work first to a local GPU worker, uses AWS only as a fallback, and returns a signed audio URL to the reader."
          width={2953}
          height={592}
        />
      </section>

      <section className="docs-prose-grid" aria-labelledby="deployment-heading">
        <div>
          <p className="kicker">AWS deployment</p>
          <h2 id="deployment-heading">A cloud fallback that does not replace local control.</h2>
          <p>
            The job API records work behind a DynamoDB conditional claim. A local
            worker can claim and synthesize first. If the job remains pending,
            Step Functions hands it to an AWS Batch GPU worker. The first valid
            claim wins.
          </p>
          <p>
            Audio objects are private by default. The API returns a short-lived
            delivery URL after the requesting site key is checked. Origin
            registration and enforcement are planned work and are not represented
            here as current controls.
          </p>
        </div>
        <Image
          src="/diagrams/aws-deployment.svg"
          alt="AWS deployment diagram with API, DynamoDB, Step Functions, AWS Batch, private audio delivery, site quotas, budget protection, and the optional local GPU path."
          width={2803}
          height={580}
        />
      </section>

      <section className="identity-section" aria-labelledby="identity-heading">
        <div className="docs-section-title">
          <p className="kicker">Operator identity</p>
          <h2 id="identity-heading">Choose the login experience your team needs.</h2>
          <p>
            The product standardizes operator access through Cognito while making
            the status of each upstream identity choice explicit.
          </p>
        </div>
        <Image
          src="/diagrams/operator-identity-options.svg"
          alt="Identity options diagram showing native Cognito users as the current path, Google as configuration-required, and IAM Identity Center as a future SAML option."
          width={970}
          height={668}
        />
        <div className="identity-grid">
          {identityOptions.map((option) => (
            <article key={option.title}>
              <p>{option.status}</p>
              <h3>{option.title}</h3>
              <span>{option.description}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="docs-security" aria-labelledby="security-heading">
        <p className="kicker">Secure-by-design workstream</p>
        <h2 id="security-heading">What is true today, and what is still being designed.</h2>
        <p>
          The current implementation has private audio, short-lived delivery,
          job-claim coordination, and cloud spend limits. Runtime origin
          enforcement and production-grade JWT validation are not complete. The
          broader threat model and control evidence are also unfinished. We will
          publish controls with their implementation and review evidence, rather
          than treating a diagram as proof.
        </p>
        <Link className="button button-outline" href="/docs/self-hosting">
          Configure your own stack
        </Link>
      </section>
    </main>
  );
}
