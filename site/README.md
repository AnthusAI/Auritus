# aurit.us marketing site

Next.js App Router site for [aurit.us](https://aurit.us): product landing,
documentation, and embed examples. It is a static export (`output: 'export'`
in `next.config.js`); there is no server runtime.

## Amplify Hosting

The repository root `amplify.yml` is the only Amplify build spec. It sets
`appRoot` to `site`, runs `npm ci` and `npm run build`, and publishes the
static export from `out/`. No server-side rendering setting is needed.

## Custom domain and DNS

Route 53 owns the `aurit.us` hosted zone. Do not let Amplify create a second
zone. In Amplify console, attach the custom domain to the existing hosted zone
so alias records point at the Amplify distribution. Details live in
`docs/DNS.md`.

Until DNS propagates, use the Amplify default domain for smoke tests.

## Local development

```bash
cd site
npm install
npm run dev
```

Set `NEXT_PUBLIC_AURITUS_API_ENDPOINT` when pointing examples at a deployed API.

## Embed script

`public/embed.js` is the built player and generator bundle from `embed/`.
Regenerate it with `make sync-embed` (or `make build-site`), which copies
`embed/dist/embed.js` here before production builds.
