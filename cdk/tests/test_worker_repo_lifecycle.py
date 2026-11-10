"""The worker image repository expires old images so storage cost stays flat."""

from __future__ import annotations

import json

from aws_cdk import App, Environment
from aws_cdk.assertions import Template
from stacks.backend import BackendStack


def test_worker_repository_keeps_only_the_newest_images() -> None:
    stack = BackendStack(
        App(),
        "TestBackend",
        env=Environment(account="123456789012", region="us-east-1"),
    )
    template = Template.from_stack(stack)
    repos = template.find_resources("AWS::ECR::Repository")
    (repo,) = repos.values()
    policy = json.loads(repo["Properties"]["LifecyclePolicy"]["LifecyclePolicyText"])
    (rule,) = policy["rules"]
    assert rule["selection"]["countType"] == "imageCountMoreThan"
    assert rule["selection"]["countNumber"] == 5
    assert rule["action"]["type"] == "expire"
