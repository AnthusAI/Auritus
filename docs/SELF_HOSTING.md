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
- `retention_days` — job/audio retention window in days; see
  [Job and audio retention](#job-and-audio-retention) below

`auritus deploy` itself does not accept arbitrary `--context` flags today, so
to set any of the knobs above (including `retention_days`) either add them to
the `"context"` object in `cdk/cdk.json` (persists across every future
deploy), or run CDK directly instead of through the wrapper:

```bash
cd cdk
npx --yes aws-cdk@2 deploy AuritusBackend --context retention_days=90
```

(`Makefile`'s `synth-cdk` target and `cli/src/auritus/commands/deploy.py` both
invoke CDK this same way — `npx --yes aws-cdk@2 ...` — so this is the
project's normal path to CDK, just with an extra `--context` flag the wrapper
doesn't expose.)

## Job and audio retention

By default, **retention is disabled** (`retention_days=0`, or unset): every
generated audio clip and every job record — including the full extracted
text of the narrated page — is kept forever. Nothing in this stack ever
deletes them on its own.

This default is deliberate, not an oversight: every DynamoDB table in this
stack uses `RemovalPolicy.RETAIN` and the audio bucket is
`auto_delete_objects=False`, so a self-hosting operator who upgrades to a
version of Auritus with this feature does not silently start losing data
they never asked to expire. Retention is opt-in.

To enable it, set `retention_days` to a positive integer (days) via one of
the two methods above, e.g. `retention_days=90`. This does two things,
both driven from that single value so they can never drift apart:

- **Job records**: the jobs DynamoDB table's `ttl` attribute is stamped on
  every job that reaches a terminal state (`done` or `failed`) with an
  expiry `retention_days` days after that job finished. Regenerating or
  retrying a job clears any stale `ttl` left over from its previous
  outcome — the new expiry is set the normal way once the job completes
  again.
- **Audio**: an S3 lifecycle rule on the audio bucket expires objects
  `retention_days` days after they were written, independently of the job
  record's own TTL.

Two things to know before enabling this in production:

- **DynamoDB TTL deletion is not instant.** AWS documents it as a
  background sweep that typically deletes expired items within 48 hours
  of their TTL timestamp, not at the exact moment it passes. Don't build
  anything that assumes an expired job record disappears the instant its
  `ttl` elapses.
- **An expired page re-triggers generation, and re-incurs GPU cost.** Once
  a job record and/or its audio has expired and been swept, a reader who
  visits the page again causes Auritus to synthesize the clip from
  scratch — the same GPU (or local worker) cost as the first time it was
  generated. Retention is a storage-cost/privacy tradeoff against that
  regeneration cost, not a free cleanup: an operator with high-traffic,
  long-lived pages that keep getting revisited after their retention
  window should weigh that cost before picking a short `retention_days`.

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
