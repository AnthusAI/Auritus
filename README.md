# Auritus

Open-source (MIT) drop-in web embed that just-in-time generates TTS audio of a
page's content. An open clone of ElevenLabs Audio Native in capability.

**Site:** [aurit.us](https://aurit.us)

## What it does

1. A generator module walks the host page DOM, applies ignore rules, and builds
   a TTS input string plus a stable content hash.
2. A player module requests (or waits for) audio for that hash and plays it.
3. A cloud backend (CDK) stores jobs behind a DynamoDB mutex. A local GPU
   worker can claim jobs; if none claims within a configurable timeout
   (default 15 minutes), Step Functions submits an AWS Batch GPU job.
4. Pluggable TTS backends: Higgs (Boson) and Qwen 3 first.

## Status

Foundations and planning are in progress. See the Kanbus board (`kbs now`)
and the milestones M0-M7 in the Initiative.

## Quick start (operators)

```bash
pip install auritus
auritus login
auritus deploy
auritus site create --origin https://example.com
auritus worker
```

Embed snippet (after `auritus site create`):

```html
<script
  src="https://aurit.us/embed.js"
  data-auritus-site-key="YOUR_SITE_KEY"
  data-auritus-name="Article title"
  data-auritus-byline="By Author"
></script>
```

## Layout

| Path | Role |
| --- | --- |
| `cli/` | Python CLI (`auritus`) |
| `cdk/` | Python CDK backend |
| `embed/` | TypeScript generator + player |
| `worker-image/` | GPU Batch container |
| `site/` | Next.js site on Amplify |
| `features/` | Gherkin specifications |
| `docs/` | Architecture and self-hosting |

## Development

```bash
make check
```

Git Flow: product PRs target `develop`. `main` is the release branch
(semantic-release + PyPI). Kanbus board commits go straight to `develop`
(no PR).

## License

MIT. See [LICENSE](LICENSE). TTS model licenses are recorded separately in
`docs/TTS_LICENSES.md`.
