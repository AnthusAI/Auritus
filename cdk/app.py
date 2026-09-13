"""Auritus CDK application entrypoint."""

from __future__ import annotations

import os

import aws_cdk as cdk
from stacks.backend import BackendStack

app = cdk.App()
BackendStack(
    app,
    "AuritusBackend",
    env=cdk.Environment(
        account=app.node.try_get_context("account")
        or os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=app.node.try_get_context("region")
        or os.environ.get("CDK_DEFAULT_REGION")
        or "us-east-1",
    ),
)
app.synth()
