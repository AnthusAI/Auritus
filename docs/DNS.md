# DNS setup for aurit.us

Route 53 owns the hosted zone. Amplify must attach as a custom domain to this
zone (do not let Amplify create a competing zone).

## Current zone (created)

- Hosted zone id: `Z0891357UAST0841IMEZ`
- Helper: `./scripts/setup-dns.sh`

### Nameservers to set at GoDaddy

Replace GoDaddy's default `domaincontrol.com` nameservers with:

```
ns-1028.awsdns-00.org
ns-74.awsdns-09.com
ns-717.awsdns-25.net
ns-1772.awsdns-29.co.uk
```

Until that change propagates, `dig NS aurit.us +short` will still show
`ns55.domaincontrol.com` / `ns56.domaincontrol.com`.

### After GoDaddy update

```bash
dig NS aurit.us +short
# expect the four awsdns-* nameservers above
```

Later: Amplify custom domain `aurit.us` / `www.aurit.us` attaches to this
existing Route 53 zone (do not let Amplify create a competing zone).
