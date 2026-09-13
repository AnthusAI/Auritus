# Self-hosting Auritus

Run the CDK backend in your AWS account, authenticate operators with Cognito
email and password, and serve audio from your stack while using the open-source
CLI and embed.

## Prerequisites

- AWS account with permissions for CDK bootstrap and deploy
- Python 3.10+, Node.js 20+ (for site/embed builds)
- A Cognito user in the deployed user pool (create in the Cognito console or
  your own provisioning flow)

Optional: a Google Cloud OAuth 2.0 client if you want Google as a Cognito
external IdP for hosted UI or future flows. It is not required for
`auritus login`.

## 1. Google OAuth client (optional Cognito IdP)

Skip this section if operators only use native pool users and
`auritus login --username`.

1. In [Google Cloud Console](https://console.cloud.google.com/), create an OAuth
   client of type **Web application**.
2. Authorized redirect URIs must include the Cognito hosted UI callback for
   your user pool (after deploy, Cognito shows the exact URL).
3. Store `client_id` and `client_secret` in the stack's Secrets Manager secret
   (`GoogleOAuthSecret`) as JSON keys `client_id` and `client_secret`, or pass
   `google_oauth_secret_arn` CDK context if you manage the secret separately.

## 2. Deploy the backend

```bash
cd /path/to/Auritus/cli
pip install -e ".[dev]"
auritus deploy
```

`auritus deploy` runs CDK against `cdk/` and writes API endpoints, Cognito ids,
and table names into the local Auritus config file.

Context knobs (optional):

- `claim_timeout_seconds` — local worker race window before Batch fallback
- `daily_site_quota` — per-site-key job creation cap
- `account` / `region` — target AWS environment

## 3. Operator login

Create a user in the Cognito user pool if you have not already, then:

```bash
auritus login --username you@example.com
```

Enter the pool password when prompted (or pass `--password`). The CLI uses
Cognito `USER_PASSWORD_AUTH`, caches short-lived JWTs under
`~/.auritus/credentials`, and uses them for subsequent `auritus site`,
`auritus worker`, and `auritus killswitch` commands.

## 4. Register a site and embed

```bash
auritus site create --origin https://your.publisher.domain
auritus player snippet --site-key <key>
```

Paste the snippet into your site. Point `data-auritus-api` at your API Gateway
URL if it differs from the default hosted endpoint.

## 5. Run a local GPU worker (recommended)

```bash
auritus worker
```

A worker on your hardware usually wins the claim race and avoids Batch GPU cost.
Configure TTS weights per [MODEL_LICENSES.md](MODEL_LICENSES.md) (runtime-fetch,
not baked into public images).

## 6. Spend guardrails

- Set an AWS Budgets daily threshold in CDK context so Batch disables when spend
  spikes.
- Use `auritus killswitch disable` for an immediate operator stop.
- Monitor per-site quota errors in API logs if embed traffic grows.

## Amplify site (optional)

The marketing/docs Next.js app in `site/` can deploy to Amplify Hosting with
your own app id. See `.github/workflows/deploy-site.yml` or host the static
embed assets from your CDN.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `auritus login` fails (wrong password, user missing) | User exists in the pool, password is correct, app client allows `USER_PASSWORD_AUTH`, local config has pool id and client id from deploy |
| Embed 403 on job create | Site key, allowed origin, quota |
| Audio never ready | Worker logs, Batch queue state, Step Functions execution |
| Batch never runs | Queue disabled by budget or kill switch |
