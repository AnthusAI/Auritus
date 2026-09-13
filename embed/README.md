# @anthusai/auritus

Drop-in browser embed for Auritus: extract page text, request TTS for a stable
content hash, and play audio when the job completes.

## Install

Publish artifacts are built to `dist/`. For local development:

```bash
cd embed
npm install
npm run build
```

## Embed snippet

After `auritus site create`, add the script to your page:

```html
<script
  src="https://aurit.us/embed.js"
  data-auritus-site-key="YOUR_SITE_KEY"
  data-auritus-name="Article title"
  data-auritus-byline="By Author"
></script>
```

The player mounts immediately after the script tag unless
`data-auritus-player-host` points at another element (CSS selector).

## Script attributes

| Attribute | Purpose |
| --- | --- |
| `data-auritus-site-key` | Required. Site key from the Auritus CLI. |
| `data-auritus-name` | Player title; falls back to `document.title`. |
| `data-auritus-byline` | Player subtitle; falls back to `location.hostname`. |
| `data-auritus-api` | API base URL (default: origin of the script URL). |
| `data-auritus-root` | CSS selector for content root (default: `document.body`). |
| `data-auritus-voice` | Voice id (default: `default`). |
| `data-auritus-tts-backend` | TTS backend (default: `kokoro`). |
| `data-auritus-ignore-selectors` | Comma-separated extra ignore selectors. |
| `data-auritus-player-host` | CSS selector where the player should mount. |

## Page markup

- `data-auritus-ignore` on an element skips that subtree.
- `data-auritus-pronounce="spoken form"` replaces the element's text for TTS.
- `data-auritus-break` inserts a pause marker in the TTS input.

Content hash includes **only** normalized text and `voice_id`.
Name, byline, and `tts_backend` affect the job and player, not the hash.

## Theming

Set CSS variables on the host page (they inherit into the shadow player):

- `--auritus-bg`
- `--auritus-fg`
- `--auritus-accent`
- `--auritus-font`
- `--auritus-radius`
- `--auritus-track`

## ESM usage

```ts
import { boot, generateTtsText, computeContentHash } from "@anthusai/auritus";

await boot();
```

The IIFE build exposes `window.Auritus` with the same exports.

## Scripts

| Command | Description |
| --- | --- |
| `npm run build` | `dist/embed.js` (IIFE) and `dist/embed.esm.js` |
| `npm run lint` | ESLint |
| `npm run test` | Vitest |
| `npm run typecheck` | `tsc --noEmit` |
