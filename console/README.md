# Auritus Operator Web Console

Operator web dashboard for [Auritus](https://aurit.us): real-time job stream monitoring, worker race observability (local GPU vs AWS Batch fallback), queue controls, and execution timelines.

## Overview

The console provides:
- **System Observability Dashboard**: High-level KPIs including 24h job volume, local vs cloud worker breakdown, average generation latency, and AWS Batch queue state.
- **Job Explorer**: Searchable and filterable table of TTS generation jobs by status (`pending`, `claimed`, `done`, `failed`) and backend engine.
- **Job Inspection & Playback**: Diagnostic timeline (requested $\to$ claimed $\to$ synthesized $\to$ done), worker attribution, and inline audio playback.
- **Worker & Queue Health**: Live monitoring and remote emergency killswitch for the AWS Batch GPU job queue.

## Authentication

Operators authenticate using the Cognito User Pool (`AuritusUsers`) via the `AuritusWebConsoleClient` provisioned in the CDK backend stack.

## Local Development

```bash
cd console
npm install
npm run dev
```

Point the console at your deployed HTTP API endpoint:
```bash
NEXT_PUBLIC_AURITUS_API_ENDPOINT=https://<api-id>.execute-api.<region>.amazonaws.com npm run dev
```
