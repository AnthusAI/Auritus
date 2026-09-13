import Link from "next/link";

const guarantees = [
  {
    title: "One login, then it runs itself",
    description:
      "Operators sign in once with a Cognito email and password. A local GPU worker then refreshes its own short-lived credentials silently, so it can backstop rendering jobs all week without asking anyone to log in again.",
  },
  {
    title: "Short-lived access, never IAM",
    description:
      "Every API call carries a one-hour Cognito JWT scoped only to operator routes. The worker never holds IAM credentials, long-lived access keys, or static API keys, and the stack mints none.",
  },
  {
    title: "Refresh-token rotation",
    description:
      "Each silent refresh issues a new refresh token with a fresh 30-day clock, so a running worker stays authenticated indefinitely. The 30-day limit only bites when a worker has been down or unreachable for more than 30 days.",
  },
  {
    title: "Revocation is the control",
    description:
      "Because a rotating token no longer self-expires while in use, auritus logout revokes it at Cognito. That is the primary stolen-token control, alongside the existing spend guardrails and kill switch.",
  },
];

export default function SecurityPage() {
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
        <p className="kicker">Security</p>
        <h1>Authentication that stays out of your way and out of your AWS account.</h1>
        <p>
          Auritus is built to run a local worker unattended for days while
          keeping credentials short-lived and narrowly scoped. The design
          avoids long-lived IAM access keys entirely and lets an operator
          revoke a compromised session in one command.
        </p>
      </header>

      <section className="docs-prose-grid" aria-labelledby="how-it-works-heading">
        <div>
          <p className="kicker">How it works</p>
          <h2 id="how-it-works-heading">One interactive login, then silent renewal.</h2>
          <p>
            An operator runs <code>auritus login</code> once and authenticates
            with a Cognito email and password. The CLI receives a one-hour
            access token and a refresh token, cached locally in a mode-0600
            file. The access token is the only credential that touches
            operator API routes, and it is scoped to those routes alone.
          </p>
          <p>
            The local worker refreshes its access token on its own, roughly
            every hour, with no browser and no MFA prompt. Refresh-token
            rotation issues a new refresh token on each renewal, so a worker
            that keeps running stays authenticated indefinitely. The 30-day
            refresh lifetime is the maximum gap between successful refreshes:
            only a worker that has been down or unable to reach Cognito for
            more than 30 days needs a human to log in again.
          </p>
        </div>
      </section>

      <section className="docs-prose-grid" aria-labelledby="notifications-heading">
        <div>
          <p className="kicker">Notifications</p>
          <h2 id="notifications-heading">The worker asks for help before it stops.</h2>
          <p>
            When a worker&apos;s refresh token is within 48 hours of expiry,
            it emails the operator through a backend alert endpoint so there is
            time to re-authenticate before jobs fall through to AWS Batch. If
            the refresh token is already dead, the worker emails again and
            exits with a distinct status code so a service supervisor can
            surface it.
          </p>
        </div>
      </section>

      <section className="identity-grid" aria-labelledby="guarantees-heading">
        <div className="docs-section-title">
          <p className="kicker">Guarantees</p>
          <h2 id="guarantees-heading">What the design promises.</h2>
        </div>
        <div className="identity-grid">
          {guarantees.map((item) => (
            <article key={item.title}>
              <h3>{item.title}</h3>
              <span>{item.description}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="docs-security" aria-labelledby="boundaries-heading">
        <p className="kicker">Boundaries</p>
        <h2 id="boundaries-heading">What this does not do.</h2>
        <p>
          The refresh token is API-scoped, not an AWS account credential.
          Auritus does not grant the worker broader IAM access, does not mint
          long-lived access keys, and does not expose static API keys. A
          leaked refresh token has the same blast radius as a leaked access
          token, only longer-lived, and is revocable through{" "}
          <code>auritus logout</code>.
        </p>
        <Link className="button button-outline" href="/docs/self-hosting">
          Configure your own stack
        </Link>
      </section>
    </main>
  );
}
