"""Step definitions for the AWS Batch fallback worker."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import httpx
from behave import given, then, when

RUNNER_PATH = Path(__file__).resolve().parents[2] / "worker-image" / "src" / "runner.py"
BATCH_ENVIRONMENT = {
    "API_URL": "https://api.auritus.test",
    "JOB_HASH": "finished-job-hash",
    "JOB_TOKEN": "revoked-worker-token",
    "AWS_BATCH_JOB_ID": "spec-batch-job",
}


def _load_runner():
    spec = importlib.util.spec_from_file_location("batch_worker_runner", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@given("the Auritus API reports the worker token for the job as not found")
def step_token_not_found(context) -> None:
    context.worker_requests = []

    def respond(method: str, url: str, **_kwargs) -> httpx.Response:
        context.worker_requests.append((method, url))
        request = httpx.Request(method, url)
        if url.endswith("/redeem"):
            return httpx.Response(
                404, json={"error": "invalid job token"}, request=request
            )
        return httpx.Response(403, json={"error": "forbidden"}, request=request)

    context.worker_responder = respond


@when("the Batch worker starts for that job")
def step_worker_starts(context) -> None:
    runner = _load_runner()
    respond = context.worker_responder
    with (
        patch.dict("os.environ", BATCH_ENVIRONMENT),
        patch.object(
            runner.httpx, "post", lambda url, **kw: respond("POST", url, **kw)
        ),
        patch.object(runner.httpx, "get", lambda url, **kw: respond("GET", url, **kw)),
        patch.object(runner.httpx, "put", lambda url, **kw: respond("PUT", url, **kw)),
        patch.object(runner, "_install_backend", lambda name: None),
    ):
        context.worker_exit_code = runner.main()


@then("the Batch worker exits successfully without claiming the job")
def step_worker_exits_cleanly(context) -> None:
    assert context.worker_exit_code == 0, context.worker_requests
    assert not any(url.endswith("/claim") for _, url in context.worker_requests)
