import { App, Stack } from "aws-cdk-lib";
import { Match, Template } from "aws-cdk-lib/assertions";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as iam from "aws-cdk-lib/aws-iam";
import * as s3 from "aws-cdk-lib/aws-s3";
import { GpuRenderFleet, SpeechRenderer } from "../src";

const image = () => "example/auritus-worker:1.2.3";

function stack(): Stack {
  return new Stack(new App(), "Host", { env: { account: "111122223333", region: "us-east-1" } });
}

describe("GpuRenderFleet", () => {
  test("scales a GPU compute environment to zero and tags its instances", () => {
    const s = stack();
    new GpuRenderFleet(s, "Fleet", { image: image(), name: "voice" });
    const t = Template.fromStack(s);

    t.hasResourceProperties("AWS::Batch::ComputeEnvironment", {
      Type: "MANAGED",
      ComputeResources: Match.objectLike({
        Type: "EC2",
        MinvCpus: 0,
        DesiredvCpus: 0,
        MaxvCpus: 8,
        InstanceTypes: ["g4dn.xlarge"],
        Tags: { "auritus:renderer": "voice" },
      }),
    });
    t.resourceCountIs("AWS::Batch::JobQueue", 1);
  });

  test("gives each job one GPU, a timeout and one retry", () => {
    const s = stack();
    new GpuRenderFleet(s, "Fleet", { image: image(), name: "voice" });

    Template.fromStack(s).hasResourceProperties("AWS::Batch::JobDefinition", {
      Type: "container",
      PlatformCapabilities: ["EC2"],
      Timeout: { AttemptDurationSeconds: 1800 },
      RetryStrategy: { Attempts: 2 },
      ContainerProperties: Match.objectLike({
        Image: "example/auritus-worker:1.2.3",
        ResourceRequirements: Match.arrayWith([
          { Type: "GPU", Value: "1" },
          { Type: "VCPU", Value: "2" },
          { Type: "MEMORY", Value: "12288" },
        ]),
      }),
    });
  });

  test("builds a public-subnet VPC with no NAT gateway unless given one", () => {
    const own = stack();
    new GpuRenderFleet(own, "Fleet", { image: image(), name: "voice" });
    const ownT = Template.fromStack(own);
    ownT.resourceCountIs("AWS::EC2::VPC", 1);
    ownT.resourceCountIs("AWS::EC2::NatGateway", 0);

    const shared = stack();
    const vpc = new ec2.Vpc(shared, "Existing", { natGateways: 0, maxAzs: 1,
      subnetConfiguration: [{ name: "Public", subnetType: ec2.SubnetType.PUBLIC }] });
    new GpuRenderFleet(shared, "Fleet", { image: image(), name: "voice", vpc });
    Template.fromStack(shared).resourceCountIs("AWS::EC2::VPC", 1);
  });
});

describe("SpeechRenderer", () => {
  function renderer(extra: Partial<ConstructorParameters<typeof SpeechRenderer>[2]> = {}) {
    const s = stack();
    const bucket = new s3.Bucket(s, "Files");
    const r = new SpeechRenderer(s, "Voice", { image: image(), name: "voice", outputBucket: bucket, ...extra });
    return { s, r, t: () => Template.fromStack(s) };
  }

  test("runs the worker image in render mode, limited to the allowed backends", () => {
    const { t } = renderer({ allowedBackends: ["kokoro"] });
    t().hasResourceProperties("AWS::Batch::JobDefinition", {
      ContainerProperties: Match.objectLike({
        Environment: Match.arrayWith([
          { Name: "AURITUS_MODE", Value: "render" },
          { Name: "AURITUS_ALLOWED_BACKENDS", Value: "kokoro" },
        ]),
      }),
    });
  });

  test("lets jobs write only under the output prefix", () => {
    const { t } = renderer({ outputPrefix: "voice-renders/" });
    const policies = t().findResources("AWS::IAM::Policy");
    const statements = Object.values(policies).flatMap(
      (p: any) => p.Properties.PolicyDocument.Statement,
    );
    const puts = statements.filter((st: any) =>
      [].concat(st.Action).some((a: string) => a.startsWith("s3:PutObject")),
    );
    expect(puts.length).toBeGreaterThan(0);
    for (const st of puts) {
      expect(JSON.stringify(st.Resource)).toContain("/voice-renders/*");
    }
    const reads = statements.filter((st: any) =>
      [].concat(st.Action).some((a: string) => a.startsWith("s3:GetObject")),
    );
    expect(reads).toHaveLength(0);
  });

  test("submits the render request to Batch and waits for it", () => {
    const { t } = renderer();
    const machines = t().findResources("AWS::StepFunctions::StateMachine");
    expect(Object.keys(machines)).toHaveLength(1);
    const definition = JSON.stringify(Object.values(machines)[0]);
    expect(definition).toContain("batch:submitJob.sync");
    expect(definition).toContain("AURITUS_RENDER_REQUEST");
    expect(definition).toContain("AURITUS_TTS_BACKEND");
    expect(definition).toContain("States.JsonToString");
  });

  test("grants a host principal permission to start renders", () => {
    const { s, r, t } = renderer();
    const role = new iam.Role(s, "Requester", { assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com") });
    r.grantStartExecution(role);
    t().hasResourceProperties("AWS::IAM::Policy", {
      Roles: [{ Ref: Match.stringLikeRegexp("Requester") }],
      PolicyDocument: {
        Statement: Match.arrayWith([Match.objectLike({ Action: "states:StartExecution" })]),
      },
    });
  });

  test("a daily budget on the renderer's own GPUs disables its queue when crossed", () => {
    const { t } = renderer({ dailyBudgetUsd: 10 });
    t().hasResourceProperties("AWS::Budgets::Budget", {
      Budget: Match.objectLike({
        BudgetType: "COST",
        TimeUnit: "DAILY",
        BudgetLimit: { Amount: 10, Unit: "USD" },
        CostFilters: { TagKeyValue: ["user:auritus:renderer$voice"] },
      }),
    });
    t().resourceCountIs("AWS::SNS::Topic", 1);
    const policies = JSON.stringify(t().findResources("AWS::IAM::Policy"));
    expect(policies).toContain("batch:UpdateJobQueue");
  });

  test("has no budget unless asked", () => {
    const { t } = renderer();
    t().resourceCountIs("AWS::Budgets::Budget", 0);
  });

  test("refuses a budget that is not positive", () => {
    expect(() => renderer({ dailyBudgetUsd: 0 })).toThrow(/dailyBudgetUsd/);
  });
});
