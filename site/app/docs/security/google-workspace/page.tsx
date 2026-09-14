import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Google Workspace SSO Integration Guide | Auritus",
  description:
    "Step-by-step instructions for configuring Google Workspace OAuth 2.0 federation with AWS Cognito, including authorized redirect URIs, JavaScript origins, and Secrets Manager setup.",
};

export default function GoogleWorkspaceDocPage() {
  return (
    <main className="documentation-page">
      <nav className="docs-nav" aria-label="Documentation navigation">
        <Link className="wordmark" href="/">
          Auritus<span>.</span>
        </Link>
        <div>
          <Link href="/docs">All docs</Link>
          <Link href="/docs/getting-started">Getting Started</Link>
          <Link href="/docs/architecture">Architecture</Link>
          <Link href="/docs/security">Security</Link>
          <Link href="/docs/self-hosting">Self-hosting</Link>
        </div>
      </nav>

      <header className="docs-hero" style={{ marginBottom: "2.5rem" }}>
        <p className="kicker">Workforce Identity</p>
        <h1>Google Workspace Single Sign-On (OAuth 2.0)</h1>
        <p>
          Configure Google Workspace as an OpenID Connect (OIDC) identity provider for your Amazon
          Cognito User Pool. Operators log in with corporate Google credentials via the CLI or web
          console, inheriting Google 2-Step Verification and organizational lifecycle controls.
        </p>
      </header>

      {/* Critical URI Reference Card */}
      <section
        style={{
          background: "var(--panel)",
          border: "2px solid var(--accent)",
          borderRadius: "12px",
          padding: "1.75rem",
          marginBottom: "3rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1rem" }}>
          <span
            style={{
              background: "var(--accent)",
              color: "#fff",
              fontSize: "0.75rem",
              fontWeight: 800,
              textTransform: "uppercase",
              padding: "0.2rem 0.6rem",
              borderRadius: "4px",
              letterSpacing: "0.08em",
            }}
          >
            Critical Configuration
          </span>
          <h2 style={{ margin: 0, fontSize: "1.3rem" }}>Exact Google Cloud Console Endpoints</h2>
        </div>
        <p style={{ color: "var(--ink-muted)", fontSize: "0.95rem", marginBottom: "1.25rem" }}>
          When creating your OAuth 2.0 Client ID in the Google Cloud Console, you must provide the
          exact Authorized JavaScript origins and Authorized redirect URIs below. Replacing{" "}
          <code>&lt;cognito-domain-prefix&gt;</code> and <code>&lt;region&gt;</code> with your stack values
          (e.g. <code>auritus-auth</code> in <code>us-east-1</code>).
        </p>

        <div style={{ display: "grid", gap: "1.25rem" }}>
          <div className="code-card">
            <div className="code-header">Authorized JavaScript origins</div>
            <pre className="code-body">
              {`https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com
http://localhost:3000
http://localhost:3001
https://console.aurit.us`}
            </pre>
          </div>

          <div className="code-card" style={{ border: "2px solid var(--highlight)" }}>
            <div className="code-header" style={{ color: "var(--highlight)", fontWeight: 800 }}>
              Authorized redirect URIs (Required by AWS Cognito IdP)
            </div>
            <pre className="code-body">
              {`https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com/oauth2/idpresponse`}
            </pre>
          </div>
        </div>

        <div
          style={{
            marginTop: "1.25rem",
            background: "var(--paper)",
            borderLeft: "4px solid var(--highlight)",
            padding: "0.85rem 1.15rem",
            borderRadius: "0 6px 6px 0",
            fontSize: "0.9rem",
          }}
        >
          <strong>Notice the <code>/oauth2/idpresponse</code> path:</strong> AWS Cognito User Pools require
          Google to redirect directly to this endpoint. If you omit <code>/oauth2/idpresponse</code> or add a
          trailing slash, Google will abort the authentication flow with{" "}
          <code style={{ color: "var(--alert)", fontWeight: 700 }}>Error 400: redirect_uri_mismatch</code>.
        </div>
      </section>

      {/* Step 1 */}
      <section style={{ marginBottom: "3rem" }}>
        <p className="kicker">Step 1</p>
        <h2 style={{ fontSize: "1.75rem", marginBottom: "0.75rem" }}>
          Configure OAuth in Google Cloud Console
        </h2>
        <p style={{ color: "var(--ink-muted)", marginBottom: "1.25rem" }}>
          Set up an OAuth 2.0 client credential in your organization&apos;s Google Cloud project.
        </p>

        <ol style={{ paddingLeft: "1.25rem", display: "grid", gap: "1rem" }}>
          <li>
            Open the{" "}
            <a
              href="https://console.cloud.google.com/apis/credentials"
              target="_blank"
              rel="noopener noreferrer"
              className="text-link"
            >
              Google Cloud Console &rarr; APIs &amp; Services &rarr; Credentials
            </a>
            .
          </li>
          <li>
            <strong>Configure OAuth consent screen</strong> (if not already completed):
            <ul style={{ marginTop: "0.5rem", display: "grid", gap: "0.4rem" }}>
              <li>
                <strong>User Type:</strong> Select <strong>Internal</strong> if you want to restrict
                operator access exclusively to members of your Google Workspace domain
                (recommended for production organizations). Select <strong>External</strong> for
                development or multi-domain environments.
              </li>
              <li>
                <strong>App Information:</strong> Set App name to <code>Auritus Operator Auth</code> and
                provide your support email.
              </li>
              <li>
                <strong>Scopes:</strong> Add <code>openid</code>,{" "}
                <code>.../auth/userinfo.email</code>, and <code>.../auth/userinfo.profile</code>.
              </li>
            </ul>
          </li>
          <li>
            <strong>Create OAuth client ID:</strong>
            <ul style={{ marginTop: "0.5rem", display: "grid", gap: "0.4rem" }}>
              <li>
                Click <strong>+ CREATE CREDENTIALS</strong> &rarr; <strong>OAuth client ID</strong>.
              </li>
              <li>
                Select <strong>Web application</strong> as the Application type.
              </li>
              <li>
                Name: <code>Auritus Cognito Federation</code>.
              </li>
              <li>
                <strong>Authorized JavaScript origins:</strong> Add your Cognito Hosted UI domain and
                console URLs:
                <pre
                  style={{
                    background: "var(--card)",
                    padding: "0.6rem 0.8rem",
                    borderRadius: "6px",
                    border: "1px solid var(--line)",
                    fontSize: "0.85rem",
                    margin: "0.4rem 0",
                  }}
                >
                  {`https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com\nhttp://localhost:3000`}
                </pre>
              </li>
              <li>
                <strong>Authorized redirect URIs:</strong> Enter the exact Cognito IdP response
                endpoint:
                <pre
                  style={{
                    background: "var(--card)",
                    padding: "0.6rem 0.8rem",
                    borderRadius: "6px",
                    border: "1px solid var(--line)",
                    fontSize: "0.85rem",
                    margin: "0.4rem 0",
                  }}
                >
                  {`https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com/oauth2/idpresponse`}
                </pre>
              </li>
              <li>
                Click <strong>CREATE</strong>. Note your <strong>Client ID</strong> and{" "}
                <strong>Client Secret</strong>.
              </li>
            </ul>
          </li>
        </ol>
      </section>

      {/* Step 2 */}
      <section style={{ marginBottom: "3rem" }}>
        <p className="kicker">Step 2</p>
        <h2 style={{ fontSize: "1.75rem", marginBottom: "0.75rem" }}>
          Store Credentials in AWS Secrets Manager
        </h2>
        <p style={{ color: "var(--ink-muted)", marginBottom: "1.25rem" }}>
          To avoid hardcoding secrets in CDK templates or source code, Auritus retrieves the Google
          OAuth credentials from AWS Secrets Manager at synth/deploy time.
        </p>

        <p>
          Store the credentials as a JSON object with keys <code>client_id</code> and{" "}
          <code>client_secret</code>:
        </p>

        <div className="code-card" style={{ marginBottom: "1rem" }}>
          <div className="code-header">AWS CLI: Store Google OAuth Credentials</div>
          <pre className="code-body">
            {`aws secretsmanager create-secret \\
  --name "auritus/google-oauth" \\
  --description "Google OAuth Client ID and Secret for Auritus Cognito IdP" \\
  --secret-string '{"client_id":"YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com","client_secret":"GOCSPX-YOUR_GOOGLE_CLIENT_SECRET"}'`}
          </pre>
        </div>

        <p style={{ fontSize: "0.9rem", color: "var(--ink-muted)" }}>
          If the secret already exists, update it with <code>aws secretsmanager put-secret-value</code>:
        </p>
        <div className="code-card">
          <div className="code-header">AWS CLI: Update Existing Secret</div>
          <pre className="code-body">
            {`aws secretsmanager put-secret-value \\
  --secret-id "auritus/google-oauth" \\
  --secret-string '{"client_id":"YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com","client_secret":"GOCSPX-YOUR_GOOGLE_CLIENT_SECRET"}'`}
          </pre>
        </div>
      </section>

      {/* Step 3 */}
      <section style={{ marginBottom: "3rem" }}>
        <p className="kicker">Step 3</p>
        <h2 style={{ fontSize: "1.75rem", marginBottom: "0.75rem" }}>
          Deploy or Update the CDK Backend
        </h2>
        <p style={{ color: "var(--ink-muted)", marginBottom: "1.25rem" }}>
          Pass the Secrets Manager ARN and your chosen Cognito domain prefix into CDK context:
        </p>

        <div className="code-card" style={{ marginBottom: "1.25rem" }}>
          <div className="code-header">CDK Deploy with Google OAuth Context</div>
          <pre className="code-body">
            {`cd cdk
cdk deploy \\
  -c google_oauth_secret_arn="arn:aws:secretsmanager:us-east-1:123456789012:secret:auritus/google-oauth" \\
  -c cognito_domain_prefix="auritus-auth"`}
          </pre>
        </div>

        <p>
          The CDK construct creates the <code>UserPoolIdentityProviderGoogle</code> resource, maps
          Google profile attributes (<code>email</code> &rarr; <code>email</code>,{" "}
          <code>name</code> &rarr; <code>fullname</code>), and attaches Google as an authorized
          identity provider on both the CLI app client and the web console app client.
        </p>
      </section>

      {/* Step 4 */}
      <section style={{ marginBottom: "3rem" }}>
        <p className="kicker">Step 4</p>
        <h2 style={{ fontSize: "1.75rem", marginBottom: "0.75rem" }}>
          Operator Authentication Workflows
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem" }}>
          <div
            style={{
              background: "var(--panel)",
              border: "1px solid var(--line)",
              borderRadius: "8px",
              padding: "1.5rem",
            }}
          >
            <h3 style={{ fontSize: "1.15rem", marginBottom: "0.5rem" }}>CLI Browser Single Sign-On</h3>
            <p style={{ fontSize: "0.9rem", color: "var(--ink-muted)", marginBottom: "1rem" }}>
              Operators run the login command. The CLI launches a temporary local loopback web server
              and opens the default browser directly to Google Sign-In:
            </p>
            <div className="code-card">
              <div className="code-header">Terminal</div>
              <pre className="code-body">auritus login --sso google</pre>
            </div>
            <p style={{ fontSize: "0.85rem", color: "var(--ink-muted)", marginTop: "0.75rem" }}>
              The browser redirects through Cognito to <code>http://localhost:8080/callback</code>. The CLI
              captures the authorization code, exchanges it for Cognito JWT tokens, and caches them in{" "}
              <code>~/.auritus/tokens.json</code> with automated 30-day rotation.
            </p>
          </div>

          <div
            style={{
              background: "var(--panel)",
              border: "1px solid var(--line)",
              borderRadius: "8px",
              padding: "1.5rem",
            }}
          >
            <h3 style={{ fontSize: "1.15rem", marginBottom: "0.5rem" }}>Operator Web Console</h3>
            <p style={{ fontSize: "0.9rem", color: "var(--ink-muted)", marginBottom: "1rem" }}>
              On the Auritus Web Console sign-in screen, operators click the Google Single Sign-On button:
            </p>
            <div
              style={{
                border: "1px solid var(--line)",
                background: "var(--card)",
                borderRadius: "6px",
                padding: "1rem",
                textAlign: "center",
                fontWeight: 600,
              }}
            >
              Sign in with Google Workspace
            </div>
            <p style={{ fontSize: "0.85rem", color: "var(--ink-muted)", marginTop: "0.75rem" }}>
              Upon successful Google authorization, Cognito redirects to{" "}
              <code>https://console.aurit.us/callback</code> or <code>http://localhost:3000/callback</code>,
              initializing an authenticated session for job exploration and worker telemetry.
            </p>
          </div>
        </div>
      </section>

      {/* Step 5: Troubleshooting */}
      <section style={{ marginBottom: "3rem" }}>
        <p className="kicker">Diagnostics</p>
        <h2 style={{ fontSize: "1.75rem", marginBottom: "1rem" }}>Troubleshooting &amp; Common Errors</h2>

        <div style={{ display: "grid", gap: "1rem" }}>
          <details
            open
            style={{
              background: "var(--card)",
              border: "1px solid var(--line)",
              borderRadius: "8px",
              padding: "1rem 1.25rem",
            }}
          >
            <summary style={{ fontWeight: 700, cursor: "pointer", color: "var(--accent)" }}>
              Error 400: redirect_uri_mismatch
            </summary>
            <div style={{ marginTop: "0.75rem", fontSize: "0.92rem", lineHeight: 1.6 }}>
              <p>
                <strong>Cause:</strong> The redirect URI sent by AWS Cognito does not exactly match any
                Authorized redirect URI configured in Google Cloud Console Credentials.
              </p>
              <p>
                <strong>Fix:</strong> In Google Cloud Console under Authorized redirect URIs, verify:
              </p>
              <ul style={{ paddingLeft: "1.2rem" }}>
                <li>
                  The URI ends with <code>/oauth2/idpresponse</code>.
                </li>
                <li>There is NO trailing slash after <code>/oauth2/idpresponse</code>.</li>
                <li>
                  The domain prefix and AWS region match your Cognito User Pool Domain exactly.
                </li>
              </ul>
            </div>
          </details>

          <details
            style={{
              background: "var(--card)",
              border: "1px solid var(--line)",
              borderRadius: "8px",
              padding: "1rem 1.25rem",
            }}
          >
            <summary style={{ fontWeight: 700, cursor: "pointer", color: "var(--accent)" }}>
              Cognito Error: redirect_mismatch
            </summary>
            <div style={{ marginTop: "0.75rem", fontSize: "0.92rem", lineHeight: 1.6 }}>
              <p>
                <strong>Cause:</strong> The callback URL requested by the Auritus CLI or Web Console is not
                in the list of allowed Callback URLs on the Cognito App Client.
              </p>
              <p>
                <strong>Fix:</strong> Ensure <code>http://localhost:8080/callback</code> and{" "}
                <code>http://127.0.0.1:8080/callback</code> are present in your CDK{" "}
                <code>AuritusCliClient</code> configuration, or <code>http://localhost:3000/callback</code> for the
                web console.
              </p>
            </div>
          </details>

          <details
            style={{
              background: "var(--card)",
              border: "1px solid var(--line)",
              borderRadius: "8px",
              padding: "1rem 1.25rem",
            }}
          >
            <summary style={{ fontWeight: 700, cursor: "pointer", color: "var(--accent)" }}>
              Cognito Error: invalid_client
            </summary>
            <div style={{ marginTop: "0.75rem", fontSize: "0.92rem", lineHeight: 1.6 }}>
              <p>
                <strong>Cause:</strong> Cognito was unable to exchange credentials with Google because the
                Client ID or Client Secret in AWS Secrets Manager is incorrect or retains placeholder values.
              </p>
              <p>
                <strong>Fix:</strong> Inspect and update your Secrets Manager secret:
              </p>
              <pre
                style={{
                  background: "var(--paper)",
                  padding: "0.5rem 0.75rem",
                  borderRadius: "4px",
                  fontSize: "0.85rem",
                }}
              >
                aws secretsmanager get-secret-value --secret-id auritus/google-oauth
              </pre>
            </div>
          </details>

          <details
            style={{
              background: "var(--card)",
              border: "1px solid var(--line)",
              borderRadius: "8px",
              padding: "1rem 1.25rem",
            }}
          >
            <summary style={{ fontWeight: 700, cursor: "pointer", color: "var(--accent)" }}>
              Access blocked: Authorization Error (Google 403)
            </summary>
            <div style={{ marginTop: "0.75rem", fontSize: "0.92rem", lineHeight: 1.6 }}>
              <p>
                <strong>Cause:</strong> The OAuth consent screen is configured as <em>Internal</em>, but the user
                attempting to sign in does not belong to your Google Workspace organization. Alternatively,
                if configured as <em>External</em> in <em>Testing</em> status, the user email has not been added to
                the Test Users list.
              </p>
              <p>
                <strong>Fix:</strong> Sign in with an authorized organizational account, or add the email
                address under <strong>OAuth consent screen &rarr; Test users</strong> in Google Cloud Console.
              </p>
            </div>
          </details>
        </div>
      </section>

      {/* Footer Navigation */}
      <div style={{ marginTop: "2rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link className="button button-primary" href="/docs/getting-started">
          &larr; Return to Getting Started Wizard
        </Link>
        <Link className="button button-outline" href="/docs/security">
          Security &amp; Token Architecture
        </Link>
      </div>
    </main>
  );
}
