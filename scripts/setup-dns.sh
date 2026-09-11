#!/usr/bin/env bash
# Create a Route 53 hosted zone for aurit.us and print NS records for GoDaddy.
# Route 53 owns the zone. Amplify must attach later as a custom domain to THIS zone.
set -euo pipefail

DOMAIN="${1:-aurit.us}"

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "AWS session expired. Run: aws login" >&2
  exit 1
fi

EXISTING=$(aws route53 list-hosted-zones-by-name --dns-name "$DOMAIN" \
  --query "HostedZones[?Name=='${DOMAIN}.'].Id" --output text)

if [[ -n "${EXISTING}" && "${EXISTING}" != "None" ]]; then
  ZONE_ID="${EXISTING##*/}"
  echo "Hosted zone already exists: ${ZONE_ID}"
else
  CALLER="auritus-$(date +%s)"
  ZONE_ID=$(aws route53 create-hosted-zone \
    --name "$DOMAIN" \
    --caller-reference "$CALLER" \
    --query 'HostedZone.Id' --output text)
  ZONE_ID="${ZONE_ID##*/}"
  echo "Created hosted zone: ${ZONE_ID}"
fi

echo
echo "Update GoDaddy nameservers for ${DOMAIN} to:"
aws route53 get-hosted-zone --id "$ZONE_ID" \
  --query 'DelegationSet.NameServers' --output text | tr '\t' '\n'
echo
echo "Verify later with: dig NS ${DOMAIN} +short"
echo "Store zone id in AGENTS.local.md as AURITUS_HOSTED_ZONE_ID=${ZONE_ID}"
