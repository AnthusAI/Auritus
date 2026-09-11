# AGENTS.md

## Project management with Kanbus

Use Kanbus for task management.
Why: Kanbus task management is MANDATORY here; every task must live in Kanbus.
When: Create/update the Kanbus task before coding; close it only after the change lands.
How: See CONTRIBUTING_AGENT.md for the Kanbus workflow, hierarchy, status rules, priorities, command examples, and the mistakes to avoid. Never inspect project/ or issue JSON directly (including with cat or jq); use Kanbus commands only.
Performance: Prefer kbs (Rust) when available; kanbus (Python) is equivalent but slower.
Warning: Editing project/ directly violates The Way. Do not read or write anything in project/; work only through Kanbus.

Kanbus board and wiki commits are **project management, not product**. After `kbs` create/update/comment/close (or a wiki edit), commit those files on `develop` and push `origin develop`. **Do not open a pull request.** Do not use a feature branch or worktree. Do not wait for CI or a reviewer. A PR is for product behavior and production code (`cli/`, `cdk/`, `embed/`, `worker-image/`, `site/`, `features/`). See CONTRIBUTING_AGENT.md.

## What this project is

Auritus is an open-source (MIT) just-in-time TTS embed for the web: a generator
that extracts page content (respecting ignore/pronounce markup), a player that
plays the narrated audio, and an AWS CDK backend with a DynamoDB mutex, a local
GPU worker race, and an AWS Batch fallback. TTS backends are pluggable (Higgs
and Qwen 3 first). The operator CLI authenticates with Cognito + Google OAuth
(`auritus login`); the browser embed uses deployer-issued site keys.

The product name is **Auritus**. The public site is **aurit.us**.

Do not describe this product as a clone, port, or copy of any third-party
product in user-facing marketing copy. Internally we may compare behavior to
Audio Native for parity checks; that language stays out of the site and README
marketing sections.

## Behavior-driven design (outside-in, for real)

Auritus is a **behavior-driven** project. Gherkin features in `features/`
are the product narrative: they tell the story of what the system is, how it
works, and how to use it. They are the primary documentation for both humans
and future agents. A new reader (person or agent) should be able to read the
`.feature` files in order and understand the system.

- **Behavior changes start in `features/`.** Write or change the Gherkin
  scenario first (Given/When/Then), then implement the steps, then the
  production code. This is outside-in. Do not write production code first and
  back-fill a scenario.
- **Stories define behavior.** Prefer Stories under Epics for specified
  behavior. Tasks and sub-tasks define implementation steps; they may not
  invent behavior beyond the specification. Do not put sub-tasks under stories.
- **`pytest` is the exception, not the default.** Use it only for pure unit
  tests of internal helpers, serializers, parsers, and coverage guards. If a
  test describes user-observable behavior, it belongs in Gherkin.
- **Regressions go to Gherkin.** When fixing a bug, add or extend a
  `.feature` scenario that fails before the fix and passes after.

## Layout

- `cli/` — `auritus` Python CLI (login, deploy, config, site, player, worker)
- `cdk/` — Python CDK backend (API Gateway, DynamoDB, Cognito, Batch, Step Functions)
- `embed/` — TypeScript generator + player drop-in (`@anthusai/auritus`)
- `worker-image/` — GPU Docker image for AWS Batch (pluggable TTS backends)
- `site/` — Next.js website for aurit.us (Amplify Hosting)
- `features/` — shared Gherkin; behavior changes start here
- `docs/` — architecture, model licenses, self-hosting, DNS
- `project/` — Kanbus board (managed by `kbs`; never hand-edit)

## Working rules

- No emojis in code, docs, commit messages, or Gherkin.
- No backward-compatibility forks or "support both ways" branches. One
  correct path. Migrate data; do not keep dual readers.
- Long, clear names. No line-level comments. Sphinx docstrings on public
  Python. TSDoc on public TypeScript exports.
- Conventional Commits. Semantic-release runs only from `main`.
- Content hash scope: `normalize(text) + voice_id + tts_backend` only.
  Name and byline are cosmetics and must not affect the hash.
- Audio is never public by default. Use short-lived signed URLs scoped to
  the requesting site key and origin.
- Do not mint long-lived IAM access keys or long-lived API keys. Prefer
  Cognito JWTs, OIDC, STS, and single-job tokens for Batch.

## Quality gates

### Python

- Black + Ruff are mandatory. `python3 -m black --check` and
  `python3 -m ruff check` must pass for `cli/` and `cdk/`.
- Sphinx-style docstrings on public symbols in `cli/src/`.
- Behavior specs via `behave`; unit tests via `pytest`.

### TypeScript

- `eslint`, `prettier --check`, and `tsc --noEmit` must pass for `embed/`
  and `site/`.

### Make

`make check` must be green before any product commit. It runs lint, specs,
coverage gates, embed build, and CDK synth.

## Git

This repository is its own git repo. Do not commit Auritus into the parent
`~/Projects` checkout.

`develop` is the continuous-integration branch. Merge accepted, green work
there as soon as it is ready. Do not park completed work on long-lived
feature branches waiting for `main`.

`main` is the release branch. Semantic-release runs only from `main`.
Do not treat a merge to `develop` as a production release.

Open pull requests against `develop` for **product** work. Merge them
there as soon as sub-agent review is addressed and CI is green. Promote
`develop` to `main` when you intend a release, not as the daily integration
path.

**Do not open a pull request for project management.** Kanbus issues,
comments, status changes, and `project/wiki` pages commit on `develop`
and push. No feature branch, no PR, no review loop. Mixing board files
into a product PR is also wrong: land the board on `develop` first.

## Cloud resources

AWS resources exist only as CDK in `cdk/`. Do not `aws s3 mb`, create
Batch environments by hand, or click a bucket into existence.
`cdk bootstrap` and `cdk deploy` (via `auritus deploy` or CI) are the
allowed AWS writes.

Route 53 owns the `aurit.us` hosted zone. Amplify attaches as a custom
domain to that existing zone. Do not let Amplify create a conflicting zone.

Spend guardrails: AWS Budgets + SNS + EventBridge disable the Batch queue
when a daily threshold is hit. Per-site-key quotas live in the router Lambda.
There is a CLI kill-switch. Do not remove these without an architect decision.

### IAM access keys (hard control)

Do **not** create IAM users or mint long-lived IAM access keys in this
repository, in CDK it deploys, or in scripts and workflows Auritus ships.
Prefer GitHub OIDC deploy roles, `sts:AssumeRole`, Cognito JWTs, and
single-job tokens for Batch. Temporary keys forwarded from an existing OIDC
or AssumeRole session are not minting; storing those values as standing
GitHub or AWS secrets is.

## Local desk configuration (`AGENTS.local.md`)

When present at the repo root, agents **must** consult `AGENTS.local.md`
for machine-specific notes: AWS account id, Amplify app id, CloudFront
domains before DNS propagates, Google OAuth client ids for Cognito, and
budget thresholds. Copy `AGENTS.local.md.example` to `AGENTS.local.md`.
That file is **gitignored and must never be committed**.

## Pull request review

No human GitHub reviewer will show up. Review is done in this session with
**Composer 2.5** (and Bugbot when a branch diff should be checked) sub-agents.
Do not mark a PR ready and wait. Launch a reviewer against `develop`, treat
request-changes as blocking, and have a second agent apply fixes. Approval
from that loop is the merge gate, not a person on the PR.

## Planning for coding agents

Stories are handed to low-parameter coding agents with step-by-step
implementation briefs (exact files, signatures, deps, acceptance test).
Those agents implement; they do not invent architecture. The architect
(this session) plans, reviews, runs acceptance, and is the sole merge gate.

## Milestones

At every milestone, launch a **sub-agent** whose only job is Kanbus and
the README. Comment on touched issues, keep statuses current, create
issues for significant new work, and update README so it matches git and
AWS. Do not fold that into the implementation agent as an afterthought.
