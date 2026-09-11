"""Shared fixtures for router Lambda tests."""

import importlib
import json
import os
import sys
from typing import Any

import boto3
import pytest
from unittest.mock import Mock
from moto import mock_aws


@pytest.fixture
def router_resources() -> dict[str, Any]:
    """Provide mocked AWS resources, environment, and API event builders."""
    with mock_aws():
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="jobs",
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
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        dynamodb.create_table(
            TableName="sites",
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
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="audio")
        os.environ.update(
            {
                "JOBS_TABLE": "jobs",
                "SITES_TABLE": "sites",
                "AUDIO_BUCKET": "audio",
                "CLOUDFRONT_DOMAIN": "audio.example.com",
                "FALLBACK_STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789012:stateMachine:fallback",
                "FALLBACK_SECONDS": "900",
                "DAILY_SITE_QUOTA": "100",
                "BATCH_JOB_QUEUE_NAME": "test-queue",
                "AWS_DEFAULT_REGION": "us-east-1",
            }
        )
        sites = boto3.resource("dynamodb", region_name="us-east-1").Table("sites")
        sites.put_item(
            Item={
                "site_id": "site-1",
                "site_key": "test-key-123",
                "origin": "https://example.com",
                "allowed_origins": ["https://example.com"],
                "daily_quota": 100,
                "disabled": False,
            }
        )
        sys.modules.pop("handler", None)
        sys.path.insert(
            0, os.path.join(os.path.dirname(__file__), "..", "lambdas", "router")
        )
        handler = importlib.import_module("handler")
        handler._sfn = Mock()

        def event(
            method: str,
            path: str,
            *,
            body: dict[str, Any] | None = None,
            headers: dict[str, str] | None = None,
            path_parameters: dict[str, str] | None = None,
        ) -> dict[str, Any]:
            """Build an API Gateway HTTP API v2 event."""
            return {
                "requestContext": {"http": {"method": method}},
                "rawPath": path,
                "headers": headers or {},
                "body": json.dumps(body) if body is not None else None,
                "pathParameters": path_parameters,
            }

        def response_body(response: dict[str, Any]) -> dict[str, Any]:
            """Decode a router response body."""
            return json.loads(response["body"])

        yield {
            "handler": handler,
            "jobs": boto3.resource("dynamodb", region_name="us-east-1").Table("jobs"),
            "sites": sites,
            "event": event,
            "response_body": response_body,
        }
        sys.path.remove(
            os.path.join(os.path.dirname(__file__), "..", "lambdas", "router")
        )
