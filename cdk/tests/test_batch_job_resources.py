"""CDK assertions for AWS Batch GPU compute sizing."""

from __future__ import annotations

from aws_cdk import App, Environment
from aws_cdk.assertions import Match, Template
from stacks.backend import BackendStack

G4DN_XLARGE_VCPUS = 4


def test_batch_gpu_job_fits_g4dn_xlarge() -> None:
    """GPU jobs must place on g4dn.xlarge with progressive allocation."""
    app = App()
    stack = BackendStack(
        app,
        "TestBackend",
        env=Environment(account="123456789012", region="us-east-1"),
    )
    template = Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::Batch::JobDefinition",
        {
            "ContainerProperties": {
                "ResourceRequirements": Match.array_with(
                    [
                        Match.object_like({"Type": "VCPU", "Value": "2"}),
                        Match.object_like({"Type": "MEMORY", "Value": "8192"}),
                        Match.object_like({"Type": "GPU", "Value": "1"}),
                    ]
                ),
                "Environment": Match.array_with(
                    [
                        Match.object_like(
                            {"Name": "AURITUS_TTS_BACKEND", "Value": "kokoro"}
                        ),
                    ]
                ),
            },
        },
    )

    template.has_resource_properties(
        "AWS::Batch::ComputeEnvironment",
        {
            "ComputeResources": Match.object_like(
                {
                    "AllocationStrategy": "BEST_FIT_PROGRESSIVE",
                    "InstanceTypes": ["g4dn.xlarge"],
                    "LaunchTemplate": Match.object_like(
                        {
                            "Version": "$Latest",
                        }
                    ),
                }
            ),
        },
    )

    template.has_resource_properties(
        "AWS::EC2::LaunchTemplate",
        {
            "LaunchTemplateData": {
                "BlockDeviceMappings": [
                    {
                        "DeviceName": "/dev/xvda",
                        "Ebs": {
                            "VolumeSize": 100,
                            "VolumeType": "gp3",
                        },
                    }
                ]
            }
        },
    )

    job_defs = template.find_resources("AWS::Batch::JobDefinition")
    assert len(job_defs) == 1

    compute_envs = template.find_resources("AWS::Batch::ComputeEnvironment")
    assert len(compute_envs) == 1

    container = next(iter(job_defs.values()))["Properties"]["ContainerProperties"]
    requirements = {
        item["Type"]: item["Value"] for item in container["ResourceRequirements"]
    }
    job_vcpus = int(requirements["VCPU"])
    instance_types = next(iter(compute_envs.values()))["Properties"][
        "ComputeResources"
    ]["InstanceTypes"]
    assert instance_types == ["g4dn.xlarge"]
    assert job_vcpus < G4DN_XLARGE_VCPUS
    assert "Vcpus" not in container
    assert "Memory" not in container
