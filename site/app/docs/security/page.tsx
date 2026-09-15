import Image from "next/image";
import Link from "next/link";

const guarantees = [
  {
    title: "The worker holds no AWS credential",
    description:
      "There is no IAM user for the worker, no access key pair, and no static API key. The stack mints none, so there is nothing on the machine that could be copied and replayed against your AWS account.",
  },
  {
    title: "Scope is structural, not a policy",
    description:
      "The operator token is a Cognito JWT accepted only by the Auritus operator routes. It cannot call AWS APIs at all. There is no policy document to get wrong, and no scope that can quietly widen over time.",
  },
  {
    title: "Rotation happens on its own",
    description:
      "Each silent refresh issues a new refresh token with a fresh 30-day clock. A running worker stays authenticated indefinitely without a human, and without anyone remembering a rotation date.",
  },
  {
    title: "Revocation is one command",
    description:
      "Token revocation is enabled on the user pool, so auritus logout invalidates the refresh token at Cognito rather than waiting for it to age out. That is the primary stolen-token control.",
  },
];

const options = [
  {
    id: "cognito",
    kicker: "Option one",
    status: "Available today",
    title: "Native Cognito users.",
    body: "The user pool holds the operator accounts directly. Self sign-up is disabled, so accounts exist only because someone with access to your AWS account created them. This is the simplest path inside your AWS account, requiring no external identity provider.",
    src: "/diagrams/auth-cognito-native.svg",
    width: 2533,
    height: 403,
    alt: "Native Cognito option: the operator runs auritus login, the CLI authenticates against a Cognito user pool with self sign-up disabled, the pool issues a one-hour access token and a rotating thirty-day refresh token, and those tokens reach operator-only routes through API Gateway and a Lambda authorizer. No IAM user, access key, or static secret is ever issued.",
  },
  {
    id: "google",
    kicker: "Option two",
    status: "Supported (SSO)",
    title: "Google Workspace.",
    body: "The stack wires a Google OAuth identity provider into the Cognito user pool. Operators authenticate with their Google account via the web console or CLI browser sign-in (`auritus login --sso google`), inheriting your Google directory MFA, password policies, and immediate offboarding controls.",
    guideHref: "/docs/security/google-workspace",
    src: "/diagrams/auth-google-workspace.svg",
    width: 2675,
    height: 403,
    alt: "Google Workspace option: the operator signs in once with a Google account, Google returns an OIDC authorization code to a Cognito user pool configured for Google federation, and the pool issues short-lived rotating tokens.",
  },
  {
    id: "identity-center",
    kicker: "Option three",
    status: "Supported (SAML 2.0 / SSO)",
    title: "AWS IAM Identity Center or any SAML provider.",
    body: "For organizations running workforce identity centrally, the Cognito user pool connects directly to AWS IAM Identity Center (AWS SSO) or any corporate SAML 2.0 provider (Okta, Entra ID, Ping). Operators sign in via single sign-on (`auritus login --sso aws-sso`), keeping operator credentials under enterprise audit governance.",
    src: "/diagrams/auth-identity-center.svg",
    width: 2862,
    height: 403,
    alt: "AWS IAM Identity Center option: a workforce user signs in through AWS IAM Identity Center or another corporate SAML provider, federates through the Cognito user pool, and receives short-lived rotating JWT tokens.",
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
          <Link href="/docs/architecture">Architecture</Link>
          <Link href="/docs/self-hosting">Self-hosting</Link>
        </div>
      </nav>

      <header className="docs-hero">
        <p className="kicker">Security</p>
        <h1>The worker never holds a key worth stealing.</h1>
        <p>
          Most breaches that begin with a machine credential begin the same way:
          a long-lived IAM access key, scoped more broadly than anyone intended,
          sitting on a host that nobody has rotated in two years. Auritus is
          built so that credential does not exist. A worker authenticates as a
          person once, then carries a one-hour token that renews itself and
          cannot reach AWS at all.
        </p>
      </header>

      <section className="docs-diagram" aria-labelledby="why-heading">
        <div className="docs-section-title">
          <p className="kicker">The problem being solved</p>
          <h2 id="why-heading">Two ways to let a machine call your service.</h2>
          <p>
            The difference is not that one is managed more carefully. It is that
            the risks people manage carefully in the first case are absent in
            the second.
          </p>
        </div>
        <Image
          src="/diagrams/iam-keys-vs-rotating-jwt.svg"
          alt="Comparison of two approaches. A conventional IAM access key is static with no expiry, scoped by a policy that is often broader than intended and drifts over time, rotated as a manual chore that gets skipped, and if leaked grants AWS API access until a human notices. An Auritus operator token expires in one hour, cannot call AWS APIs at all and is limited to operator routes, rotates automatically on every refresh, and if leaked is valid for at most an hour and revocable with auritus logout."
          width={1826}
          height={492}
        />
      </section>

      <section className="docs-prose-single" aria-labelledby="threat-heading">
        <div>
          <p className="kicker">Risk moved into the architecture</p>
          <h2 id="threat-heading">Fewer things an operator can get wrong.</h2>
          <p>
            An IAM access key is dangerous less because it is weak than because
            keeping it safe is an ongoing human obligation. Someone has to write
            a tight policy, resist widening it when something breaks at 2am,
            rotate the key on schedule, and remember every host it was copied
            to. Each of those is a place an organization can quietly fall
            behind, and none of them announce failure.
          </p>
          <p>
            Auritus removes the obligations rather than documenting them. The
            long-lived artifact on the machine is a Cognito refresh token, which
            is not an AWS credential and cannot be presented to any AWS API. The
            credential that does reach the service expires in an hour. Rotation
            is a property of the refresh exchange, so it cannot be skipped under
            load. What remains is a single decision, made once, about who is
            allowed to be an operator.
          </p>
        </div>
      </section>

      <section className="docs-diagram" aria-labelledby="lifecycle-heading">
        <div className="docs-section-title">
          <p className="kicker">How the worker stays authenticated</p>
          <h2 id="lifecycle-heading">
            One login, then indefinitely, if it keeps trying.
          </h2>
          <p>
            The thirty-day number is not a deadline for the operator. It is the
            longest the worker may stay silent.
          </p>
        </div>
        <Image
          src="/diagrams/worker-token-lifecycle.svg"
          alt="Token lifecycle in three stages. Once, with a human present: auritus login authenticates against Cognito, which issues a one-hour access token and a thirty-day refresh token. Steady state with no human, indefinitely: the worker calls the API with the bearer access token, silently refreshes before the hour is up, and rotation issues a new refresh token that resets the thirty-day clock, repeating forever. Only if the worker goes quiet: forty-eight hours before expiry it emails the operator, and past thirty days idle the refresh is rejected, the worker stops, and re-login is required."
          width={3221}
          height={411}
        />
      </section>

      <section
        className="docs-prose-single"
        aria-labelledby="mechanics-heading"
      >
        <div>
          <p className="kicker">The mechanics</p>
          <h2 id="mechanics-heading">Why a thirty-day token lasts forever.</h2>
          <p>
            An operator runs <code>auritus login</code> once. Cognito returns an
            access token valid for one hour and a refresh token valid for thirty
            days, cached in a mode-0600 file. Before the access token expires
            the CLI exchanges the refresh token for a new pair, with no browser
            and no prompt.
          </p>
          <p>
            The part that matters is rotation. The user pool is configured to
            return a <em>new</em> refresh token on every exchange, so each
            successful renewal resets the thirty-day clock. A worker refreshing
            hourly is never within twenty-nine days of expiry. The thirty-day
            limit only applies to a worker that has been powered off, offline,
            or otherwise unable to reach Cognito for a month.
          </p>
          <p>
            That boundary is signposted rather than sprung. Starting forty-eight
            hours before expiry, the worker emails the operator, at most once a
            day. If the refresh token is already dead it emails again and exits
            with a distinct status code so a supervisor can surface it. That
            alert route is deliberately unauthenticated: a worker whose token
            has expired cannot present one, which is exactly when it needs to
            ask for help. Abuse is bounded by confirming the address belongs to
            a real Cognito user and by a per-recipient rate limit.
          </p>
        </div>
      </section>

      <section className="identity-section" aria-labelledby="options-heading">
        <div className="docs-section-title">
          <p className="kicker">Operator identity</p>
          <h2 id="options-heading">
            Three ways to decide who may be an operator.
          </h2>
          <p>
            All three converge on the same Cognito pool and therefore the same
            short-lived, rotating, API-scoped token. Only the question of who
            gets in changes. Their implementation status differs, and is stated
            with each.
          </p>
        </div>
        {options.map((option) => (
          <section
            className="identity-option"
            key={option.id}
            aria-labelledby={`${option.id}-heading`}
          >
            <div className="docs-section-title">
              <p className="kicker">
                {option.kicker} &mdash; {option.status}
              </p>
              <h3 id={`${option.id}-heading`}>{option.title}</h3>
              <p>{option.body}</p>
              {option.guideHref && (
                <p style={{ marginTop: "0.75rem" }}>
                  <Link href={option.guideHref} className="text-link" style={{ fontWeight: 700 }}>
                    View complete setup guide &amp; OAuth endpoints &rarr;
                  </Link>
                </p>
              )}
            </div>
            <Image
              src={option.src}
              alt={option.alt}
              width={option.width}
              height={option.height}
            />
          </section>
        ))}
      </section>

      <section className="guarantee-section" aria-labelledby="guarantees-heading">
        <div className="docs-section-title">
          <p className="kicker">Guarantees</p>
          <h2 id="guarantees-heading">What the design promises.</h2>
        </div>
        <div className="guarantee-grid">
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
        <h2 id="boundaries-heading">What is not true yet.</h2>
        <p>
          Everything above describes the architecture. One part of it is not
          fully enforced in the current implementation, and we would rather say
          so here than have you discover it in the source.
        </p>
        <p>
          <strong>
            The API authorizer does not verify token signatures yet.
          </strong>{" "}
          It checks that a bearer token is present, that it is shaped like a
          JWT, and that the issuer and audience claims match this deployment.
          Those claims are not secret, so a forged token carrying the right
          values would currently be accepted. Full RS256 verification against
          the Cognito JWKS needs a Lambda layer with the signing libraries, and
          it is the next piece of this work. Until it lands, treat the operator
          API as protected by obscurity of the endpoint rather than by the
          token.
        </p>
        <p>
          The claims that do hold today are the ones about what is absent: the
          worker is issued no IAM user, no access key pair, and no static API
          key, and the token it does carry cannot call AWS APIs. A leaked
          refresh token has the blast radius of a leaked access token, longer
          lived, and is revocable with <code>auritus logout</code>.
        </p>
        <Link className="button button-outline" href="/docs/self-hosting">
          Configure your own stack
        </Link>
      </section>
    </main>
  );
}
