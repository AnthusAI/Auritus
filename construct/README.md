# Auritus construct

AWS CDK constructs for rendering [Auritus](https://github.com/AnthusAI/Auritus) speech on AWS Batch GPUs, in any application's own AWS account. It's published for TypeScript (`@anthusai/auritus-construct` on npm) and Python (`auritus-construct` on PyPI) from one jsii source.

- **`GpuRenderFleet`**: Batch GPU capacity that runs the Auritus worker image. The compute environment (default `g4dn.xlarge`) scales to zero, so an idle fleet costs nothing. It comes with a queue and a one-GPU job definition.
- **`SpeechRenderer`**: a fleet plus a Step Functions state machine. Each execution renders one request into your S3 bucket.

## Use

```ts
import { SpeechRenderer } from "@anthusai/auritus-construct";

const renderer = new SpeechRenderer(stack, "Voice", {
  name: "myapp-voice",
  image: "123456789012.dkr.ecr.us-east-1.amazonaws.com/auritus-worker:1.4.0",
  outputBucket: bucket,
  outputPrefix: "voice-renders/",
  allowedBackends: ["kokoro"],
  dailyBudgetUsd: 10,
});
renderer.grantStartExecution(requestFunction);
```

Start an execution with every key present (`speed` and `seed` may be `null`):

```json
{ "jobId": "job-123", "text": "Welcome to the show.", "voice": "kokoro:am_adam", "speed": 1.1, "seed": null }
```

The job writes under `s3://<bucket>/<outputPrefix><jobId>/`:
- **On success:** `speech.wav` (mono 16-bit), and `speech.json` with the sample rate, duration, segments, provenance and request key.
- **On failure:** `error.json`, and the execution fails.

To follow progress, use EventBridge "Step Functions Execution Status Change" events for `renderer.stateMachine`.

## The daily budget

`dailyBudgetUsd` creates an AWS Budget scoped to the fleet's GPU instances through their `auritus:renderer` tag. When it's crossed, the queue is disabled, so new renders fail at once instead of waiting. Re-enable the queue to resume.

- **Activate the tag first.** Activate the `auritus:renderer` cost allocation tag once in the account's Billing console; otherwise the budget sees no cost.
- **It's a backstop, not a hard limit.** AWS reports costs hours late.
