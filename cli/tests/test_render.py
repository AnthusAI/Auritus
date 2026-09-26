"""The render mode writes to S3 when its output is an s3:// URI."""

from __future__ import annotations

import json

import boto3
from moto import mock_aws

from auritus.render import main


@mock_aws
def test_render_writes_speech_and_metadata_to_s3() -> None:
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="host-bucket")
    request = {
        "text": "Hello there.",
        "voice": "fake:plain",
        "output": "s3://host-bucket/voice-renders/job-1",
    }

    assert main({"AURITUS_RENDER_REQUEST": json.dumps(request)}) == 0

    keys = {
        o["Key"]
        for o in s3.list_objects_v2(Bucket="host-bucket", Prefix="voice-renders/")[
            "Contents"
        ]
    }
    assert keys == {"voice-renders/job-1/speech.wav", "voice-renders/job-1/speech.json"}
    wav = s3.get_object(Bucket="host-bucket", Key="voice-renders/job-1/speech.wav")
    assert wav["ContentType"] == "audio/wav"
    meta = json.loads(
        s3.get_object(Bucket="host-bucket", Key="voice-renders/job-1/speech.json")[
            "Body"
        ].read()
    )
    assert meta["request"]["voice"] == "fake:plain"
    assert meta["provenance"]["backend"] == "fake"


@mock_aws
def test_render_failure_writes_error_json_to_s3() -> None:
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="host-bucket")
    request = {"text": "", "voice": "fake:plain", "output": "s3://host-bucket/r/2"}

    assert main({"AURITUS_RENDER_REQUEST": json.dumps(request)}) == 1

    error = json.loads(
        s3.get_object(Bucket="host-bucket", Key="r/2/error.json")["Body"].read()
    )
    assert error["error"] == "InvalidRequest"
