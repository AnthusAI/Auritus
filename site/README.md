# aurit.us marketing site

Next.js App Router site for [aurit.us](https://aurit.us): product landing,
documentation, and embed examples.

## Amplify Hosting

`amplify.yml` runs `npm ci` and `npm run build` in this directory. Connect the
Amplify app to the Auritus GitHub repository with `appRoot` set to `site/` (or
build from this folder in monorepo-aware CI).

Artifacts use the default Next.js output (`.next`). Enable SSR on Amplify for
App Router routes.

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

`public/embed.js` is a placeholder. Release pipelines should copy
`embed/dist` output here (or to the CDN origin) before production builds.
