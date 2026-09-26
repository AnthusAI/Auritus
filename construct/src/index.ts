/**
 * AWS CDK constructs for rendering Auritus speech on AWS Batch GPUs.
 *
 * - {@link GpuRenderFleet}: the Batch GPU capacity (scale-to-zero compute
 *   environment, queue and job definition) that runs the Auritus worker image.
 * - {@link SpeechRenderer}: a fleet plus a state machine that renders one
 *   request into the host's S3 bucket, so any application can have speech
 *   rendered in its own AWS account without the Auritus web service.
 */
import { Duration, Stack } from "aws-cdk-lib";
import * as batch from "aws-cdk-lib/aws-batch";
import * as budgets from "aws-cdk-lib/aws-budgets";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sns from "aws-cdk-lib/aws-sns";
import * as subscriptions from "aws-cdk-lib/aws-sns-subscriptions";
import * as sfn from "aws-cdk-lib/aws-stepfunctions";
import * as tasks from "aws-cdk-lib/aws-stepfunctions-tasks";
import { Construct } from "constructs";

/** The EC2 tag every fleet instance carries: key `auritus:renderer`, value the fleet's name. */
export const RENDERER_TAG_KEY = "auritus:renderer";

/** Properties for {@link GpuRenderFleet}. */
export interface GpuRenderFleetProps {
  /** Worker image URI, e.g. `123456789012.dkr.ecr.us-east-1.amazonaws.com/auritus-worker:1.4.0`. */
  readonly image: string;
  /**
   * Names this fleet. It becomes the `auritus:renderer` tag on its GPU
   * instances, which scopes cost reports and budgets to this fleet.
   */
  readonly name: string;
  /** VPC for the GPU instances. @default a new two-AZ VPC with public subnets and no NAT gateway */
  readonly vpc?: ec2.IVpc;
  /** EC2 instance types. @default ["g4dn.xlarge"] */
  readonly instanceTypes?: string[];
  /** Most vCPUs running at once (each job takes 2). @default 8 */
  readonly maxvCpus?: number;
  /** How long one job attempt may run. @default Duration.minutes(30) */
  readonly jobTimeout?: Duration;
  /** Extra environment for every job. @default none */
  readonly environment?: { [name: string]: string };
}

/**
 * Batch GPU capacity running the Auritus worker image: a compute environment
 * that scales to zero when idle, a queue, and a one-GPU job definition.
 */
export class GpuRenderFleet extends Construct {
  /** ARN of the job queue. */
  public readonly jobQueueArn: string;
  /** ARN of the job definition. */
  public readonly jobDefinitionArn: string;
  /** Role the worker container runs as; grant it what jobs need. */
  public readonly jobRole: iam.Role;
  /** The VPC the GPU instances run in. */
  public readonly vpc: ec2.IVpc;

  constructor(scope: Construct, id: string, props: GpuRenderFleetProps) {
    super(scope, id);

    this.vpc =
      props.vpc ??
      new ec2.Vpc(this, "Vpc", {
        maxAzs: 2,
        natGateways: 0,
        subnetConfiguration: [{ name: "Public", subnetType: ec2.SubnetType.PUBLIC, cidrMask: 18 }],
      });
    const securityGroup = new ec2.SecurityGroup(this, "SecurityGroup", {
      vpc: this.vpc,
      allowAllOutbound: true,
    });
    const instanceRole = new iam.Role(this, "InstanceRole", {
      assumedBy: new iam.ServicePrincipal("ec2.amazonaws.com"),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName("service-role/AmazonEC2ContainerServiceforEC2Role"),
      ],
    });
    const instanceProfile = new iam.CfnInstanceProfile(this, "InstanceProfile", {
      roles: [instanceRole.roleName],
    });
    // Model images and weights are large; the default 30 GB root fills up.
    const launchTemplate = new ec2.LaunchTemplate(this, "LaunchTemplate", {
      blockDevices: [
        {
          deviceName: "/dev/xvda",
          volume: ec2.BlockDeviceVolume.ebs(100, { volumeType: ec2.EbsDeviceVolumeType.GP3 }),
        },
      ],
    });

    const computeEnvironment = new batch.CfnComputeEnvironment(this, "ComputeEnvironment", {
      type: "MANAGED",
      computeResources: {
        type: "EC2",
        minvCpus: 0,
        desiredvCpus: 0,
        maxvCpus: props.maxvCpus ?? 8,
        instanceTypes: props.instanceTypes ?? ["g4dn.xlarge"],
        allocationStrategy: "BEST_FIT_PROGRESSIVE",
        subnets: this.vpc.publicSubnets.map((s) => s.subnetId),
        securityGroupIds: [securityGroup.securityGroupId],
        instanceRole: instanceProfile.attrArn,
        launchTemplate: {
          launchTemplateId: launchTemplate.launchTemplateId,
          version: "$Latest",
        },
        tags: { [RENDERER_TAG_KEY]: props.name },
      },
    });

    const queue = new batch.CfnJobQueue(this, "JobQueue", {
      priority: 1,
      state: "ENABLED",
      computeEnvironmentOrder: [{ order: 1, computeEnvironment: computeEnvironment.ref }],
    });
    this.jobQueueArn = queue.attrJobQueueArn;

    this.jobRole = new iam.Role(this, "JobRole", {
      assumedBy: new iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
    });
    const jobDefinition = new batch.CfnJobDefinition(this, "JobDefinition", {
      type: "container",
      platformCapabilities: ["EC2"],
      timeout: { attemptDurationSeconds: (props.jobTimeout ?? Duration.minutes(30)).toSeconds() },
      // One retry, for transient trouble such as an instance failing to boot.
      retryStrategy: { attempts: 2 },
      containerProperties: {
        image: props.image,
        jobRoleArn: this.jobRole.roleArn,
        resourceRequirements: [
          { type: "GPU", value: "1" },
          { type: "VCPU", value: "2" },
          { type: "MEMORY", value: "12288" },
        ],
        environment: Object.entries(props.environment ?? {}).map(([name, value]) => ({ name, value })),
        logConfiguration: { logDriver: "awslogs" },
      },
    });
    this.jobDefinitionArn = jobDefinition.ref;
  }
}

/** Properties for {@link SpeechRenderer}. */
export interface SpeechRendererProps extends GpuRenderFleetProps {
  /** Bucket the rendered speech is written to. */
  readonly outputBucket: s3.IBucket;
  /**
   * Key prefix for results; each render writes under `<prefix><jobId>/`:
   * `speech.wav` and `speech.json`, or `error.json`. @default "voice-renders/"
   */
  readonly outputPrefix?: string;
  /** Backends this deployment will run; others are refused. @default ["kokoro"] */
  readonly allowedBackends?: string[];
  /**
   * Daily cost cap in USD for this fleet's GPU instances (by their
   * `auritus:renderer` tag). Crossing it disables the queue, so later renders
   * fail at once instead of waiting. Re-enable the queue to resume.
   *
   * The `auritus:renderer` cost allocation tag must be activated once in the
   * account's Billing console, and AWS reports costs hours late, so this is a
   * backstop, not a hard limit. @default no budget
   */
  readonly dailyBudgetUsd?: number;
}

/**
 * Renders one speech request per state-machine execution on a
 * {@link GpuRenderFleet}.
 *
 * Start an execution with
 * `{"jobId": "...", "text": "...", "voice": "kokoro:af_heart", "speed": null, "seed": null}`
 * (every key present; `speed` and `seed` may be null). The execution succeeds
 * once `<outputPrefix><jobId>/speech.wav` and `speech.json` are written, and
 * fails otherwise. Watch it with EventBridge "Step Functions Execution Status
 * Change" events for {@link stateMachine}.
 */
export class SpeechRenderer extends Construct {
  /** The GPU capacity renders run on. */
  public readonly fleet: GpuRenderFleet;
  /** One execution renders one request. */
  public readonly stateMachine: sfn.StateMachine;
  /** Normalized output prefix, ending in `/`. */
  public readonly outputPrefix: string;

  constructor(scope: Construct, id: string, props: SpeechRendererProps) {
    super(scope, id);
    if (props.dailyBudgetUsd !== undefined && !(props.dailyBudgetUsd > 0)) {
      throw new Error(`dailyBudgetUsd must be positive; got ${props.dailyBudgetUsd}`);
    }
    const prefix = (props.outputPrefix ?? "voice-renders/").replace(/^\/+/, "");
    this.outputPrefix = prefix.endsWith("/") ? prefix : `${prefix}/`;
    const allowed = props.allowedBackends ?? ["kokoro"];

    this.fleet = new GpuRenderFleet(this, "Fleet", {
      ...props,
      environment: {
        ...(props.environment ?? {}),
        AURITUS_MODE: "render",
        AURITUS_ALLOWED_BACKENDS: allowed.join(","),
      },
    });
    props.outputBucket.grantPut(this.fleet.jobRole, `${this.outputPrefix}*`);

    const build = new sfn.Pass(this, "BuildRequest", {
      parameters: {
        "jobId.$": "$.jobId",
        backend: sfn.JsonPath.arrayGetItem(sfn.JsonPath.stringSplit(sfn.JsonPath.stringAt("$.voice"), ":"), 0),
        render: {
          "text.$": "$.text",
          "voice.$": "$.voice",
          "speed.$": "$.speed",
          "seed.$": "$.seed",
          output: sfn.JsonPath.format(
            `s3://${props.outputBucket.bucketName}/${this.outputPrefix}{}`,
            sfn.JsonPath.stringAt("$.jobId"),
          ),
        },
      },
    });
    const serialize = new sfn.Pass(this, "SerializeRequest", {
      parameters: {
        "jobId.$": "$.jobId",
        "backend.$": "$.backend",
        "output.$": "$.render.output",
        request: sfn.JsonPath.jsonToString(sfn.JsonPath.objectAt("$.render")),
      },
    });
    const submit = new tasks.BatchSubmitJob(this, "Render", {
      jobName: "auritus-render",
      jobQueueArn: this.fleet.jobQueueArn,
      jobDefinitionArn: this.fleet.jobDefinitionArn,
      integrationPattern: sfn.IntegrationPattern.RUN_JOB,
      containerOverrides: {
        environment: {
          AURITUS_RENDER_REQUEST: sfn.JsonPath.stringAt("$.request"),
          AURITUS_TTS_BACKEND: sfn.JsonPath.stringAt("$.backend"),
        },
      },
      resultPath: sfn.JsonPath.DISCARD,
    });
    const failed = new sfn.Fail(this, "RenderFailed", {
      error: "RenderFailed",
      cause: "The render job failed or could not start; see <output>/error.json and the job's logs.",
    });
    submit.addCatch(failed, { errors: [sfn.Errors.ALL] });
    const done = new sfn.Pass(this, "Rendered", {
      parameters: { "jobId.$": "$.jobId", "output.$": "$.output" },
    });

    this.stateMachine = new sfn.StateMachine(this, "StateMachine", {
      definitionBody: sfn.DefinitionBody.fromChainable(build.next(serialize).next(submit).next(done)),
      timeout: Duration.hours(1),
    });

    if (props.dailyBudgetUsd !== undefined) {
      this.addBudgetGuard(props.name, props.dailyBudgetUsd);
    }
  }

  /** Allow `grantee` to start renders. */
  public grantStartExecution(grantee: iam.IGrantable): iam.Grant {
    return this.stateMachine.grantStartExecution(grantee);
  }

  private addBudgetGuard(name: string, limit: number): void {
    const topic = new sns.Topic(this, "BudgetTopic");
    topic.addToResourcePolicy(
      new iam.PolicyStatement({
        actions: ["sns:Publish"],
        principals: [new iam.ServicePrincipal("budgets.amazonaws.com")],
        resources: [topic.topicArn],
        conditions: { StringEquals: { "aws:SourceAccount": Stack.of(this).account } },
      }),
    );
    new budgets.CfnBudget(this, "DailyBudget", {
      budget: {
        budgetType: "COST",
        timeUnit: "DAILY",
        budgetLimit: { amount: limit, unit: "USD" },
        costFilters: { TagKeyValue: [`user:${RENDERER_TAG_KEY}$${name}`] },
      },
      notificationsWithSubscribers: [
        {
          notification: {
            comparisonOperator: "GREATER_THAN",
            notificationType: "ACTUAL",
            threshold: 100,
            thresholdType: "PERCENTAGE",
          },
          subscribers: [{ address: topic.topicArn, subscriptionType: "SNS" }],
        },
      ],
    });
    const guard = new lambda.Function(this, "BudgetGuard", {
      runtime: lambda.Runtime.NODEJS_20_X,
      handler: "index.handler",
      timeout: Duration.seconds(30),
      environment: { JOB_QUEUE_ARN: this.fleet.jobQueueArn },
      code: lambda.Code.fromInline(
        [
          'const { BatchClient, UpdateJobQueueCommand } = require("@aws-sdk/client-batch");',
          "exports.handler = async () => {",
          "  await new BatchClient({}).send(",
          '    new UpdateJobQueueCommand({ jobQueue: process.env.JOB_QUEUE_ARN, state: "DISABLED" }),',
          "  );",
          '  console.log("disabled", process.env.JOB_QUEUE_ARN);',
          '  return { state: "DISABLED" };',
          "};",
        ].join("\n"),
      ),
    });
    guard.addToRolePolicy(
      new iam.PolicyStatement({ actions: ["batch:UpdateJobQueue"], resources: [this.fleet.jobQueueArn] }),
    );
    topic.addSubscription(new subscriptions.LambdaSubscription(guard));
  }
}
