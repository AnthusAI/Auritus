# DNS setup for aurit.us

Route 53 owns the hosted zone. Amplify must attach as a custom domain to this
zone (do not let Amplify create a competing zone).

## Steps

1. Create hosted zone:

```bash
aws route53 create-hosted-zone --name aurit.us --caller-reference "auritus-$(date +%s)"
```

2. Capture the four NS records from the zone.

3. In GoDaddy DNS for `aurit.us`, replace nameservers with the Route 53 NS set.

4. Verify delegation:

```bash
dig NS aurit.us +short
```

5. Later: Amplify custom domain `aurit.us` / `www.aurit.us` using the existing
   hosted zone (Route 53 records, not Amplify-managed zone creation).
