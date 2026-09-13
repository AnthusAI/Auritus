"""Auritus CDK application entrypoint."""

from __future__ import annotations

import aws_cdk as cdk
from stacks.backend import BackendStack

app = cdk.App()
BackendStack(
    app,
    "AuritusBackend",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region") or "us-east-1",
    ),
)
app.synth()
