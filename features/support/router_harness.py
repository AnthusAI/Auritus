"""In-process router Lambda harness for Auritus specs.

Starts a moto mock scoped to the scenario, creates uniquely named jobs and
sites tables and an audio bucket, points the router's environment at them,
and loads a fresh copy of the router handler with Step Functions and Batch
replaced by mocks.
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import boto3
from moto import mock_aws

from support.operator_tokens import install_test_user_pool

LAMBDAS_PATH = Path(__file__).resolve().parents[2] / "cdk" / "lambdas"


@dataclass
class RouterHarness:
    """A loaded router handler and the tables it writes to."""

    router: Any
    jobs_table: Any
    sites_table: Any

    def call(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        path_parameters: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Invoke the router with an API Gateway HTTP API v2 event.

        :param method: HTTP method.
        :param path: Raw request path.
        :param headers: Request headers.
        :param body: JSON request body.
        :param path_parameters: Route path parameters.
        :returns: The router's proxy response.
        """
        return self.router.handler(
            {
                "requestContext": {"http": {"method": method}},
                "rawPath": path,
                "headers": headers or {},
                "body": json.dumps(body) if body is not None else None,
                "pathParameters": path_parameters,
                "queryStringParameters": None,
            },
            None,
        )

    def register_site(self, site_key: str) -> None:
        """Store an enabled site that owns a site key.

        :param site_key: The public site key to register.
        """
        self.sites_table.put_item(
            Item={
                "site_id": f"site-{site_key}",
                "site_key": site_key,
                "allowed_origins": ["https://example.com"],
                "daily_quota": 100,
                "disabled": False,
            }
        )


def start_router(context) -> RouterHarness:
    """Start a scenario-scoped router with empty tables.

    :param context: The behave context; mocks and environment are undone by
        scenario cleanups.
    :returns: The loaded router harness.
    """
    aws_mock = mock_aws()
    aws_mock.start()
    context.add_cleanup(aws_mock.stop)
    install_test_user_pool()
    suffix = uuid.uuid4().hex[:12]
    jobs_table = f"spec-jobs-{suffix}"
    sites_table = f"spec-sites-{suffix}"
    audio_bucket = f"spec-audio-{suffix}"
    environment = patch.dict(
        os.environ,
        {
            "JOBS_TABLE": jobs_table,
            "SITES_TABLE": sites_table,
            "AUDIO_BUCKET": audio_bucket,
            "AWS_DEFAULT_REGION": "us-east-1",
        },
    )
    environment.start()
    context.add_cleanup(environment.stop)
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName=jobs_table,
        KeySchema=[{"AttributeName": "content_hash", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "content_hash", "AttributeType": "S"},
            {"AttributeName": "status", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "status-created_at-index",
                "KeySchema": [
                    {"AttributeName": "status", "KeyType": "HASH"},
                    {"AttributeName": "created_at", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    dynamodb.create_table(
        TableName=sites_table,
        KeySchema=[{"AttributeName": "site_id", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "site_id", "AttributeType": "S"},
            {"AttributeName": "site_key", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "site_key-index",
                "KeySchema": [{"AttributeName": "site_key", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    boto3.client("s3", region_name="us-east-1").create_bucket(Bucket=audio_bucket)
    router_path = str(LAMBDAS_PATH / "router")
    if router_path not in sys.path:
        sys.path.insert(0, router_path)
    sys.modules.pop("handler", None)
    router = importlib.import_module("handler")
    router._sfn = Mock()
    router._batch = Mock()
    router._batch.describe_job_queues.return_value = {
        "jobQueues": [{"state": "ENABLED"}]
    }
    resource = boto3.resource("dynamodb", region_name="us-east-1")
    return RouterHarness(
        router=router,
        jobs_table=resource.Table(jobs_table),
        sites_table=resource.Table(sites_table),
    )
