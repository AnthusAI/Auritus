"""Behave steps for content hash scope scenarios."""

from __future__ import annotations

import json

from behave import given, then, when
from common_steps import _hash

from support.router_harness import start_router


@when('the TTS text becomes "{text}"')
def step_text_becomes(context, text: str) -> None:
    context.tts_text = text


@when("the content hash is computed again")
def step_compute_again(context) -> None:
    context.hash_other = _hash(context.tts_text, context.voice_id, context.tts_backend)


@then("the two content hashes match")
def step_hashes_match(context) -> None:
    assert context.hash == context.hash_other


SPEC_SITE_KEY = "content-hash-spec-site-key"
TEXT_FIXTURES = {
    "a decomposed accent between Unicode spaces": "Cafe\u0301\u00a0\u2003bar\ufeff",
}


def _fixture_text(fixture: str) -> str:
    if fixture in TEXT_FIXTURES:
        return TEXT_FIXTURES[fixture]
    prefix = 'the text "'
    assert fixture.startswith(prefix) and fixture.endswith('"'), fixture
    return fixture[len(prefix) : -1].replace("\\n", "\n")


def _create_job(context, body: dict) -> None:
    context.create_response = context.hash_router.call(
        "POST", "/jobs", headers={"x-auritus-site-key": SPEC_SITE_KEY}, body=body
    )
    context.create_body = json.loads(context.create_response["body"])


@given("a registered site key")
def step_registered_site_key(context) -> None:
    context.hash_router = start_router(context)
    context.hash_router.register_site(SPEC_SITE_KEY)


@when('a job is created for {fixture} with voice "{voice_id}" on "{tts_backend}"')
def step_create_job_for_fixture(
    context, fixture: str, voice_id: str, tts_backend: str
) -> None:
    text = _fixture_text(fixture)
    _create_job(
        context,
        {
            "text": text,
            "voice_id": voice_id,
            "tts_backend": tts_backend,
            "content_hash": _hash(text, voice_id, tts_backend),
        },
    )


@when('a job is created for the text "{text}" claiming the content hash of "{victim}"')
def step_create_job_with_foreign_hash(context, text: str, victim: str) -> None:
    context.victim_hash = _hash(victim, "af_heart", "kokoro")
    _create_job(
        context,
        {
            "text": text,
            "voice_id": "af_heart",
            "tts_backend": "kokoro",
            "content_hash": context.victim_hash,
        },
    )


@then('the job is created with content hash "{content_hash}"')
def step_job_created_with_hash(context, content_hash: str) -> None:
    assert context.create_response["statusCode"] == 201, context.create_response
    assert context.create_body["content_hash"] == content_hash, context.create_body


@then('the stored job text is "{normalized_text}"')
def step_stored_text(context, normalized_text: str) -> None:
    item = context.hash_router.jobs_table.get_item(
        Key={"content_hash": context.create_body["content_hash"]}
    )["Item"]
    assert item["text"] == normalized_text, item["text"]


@then('the API rejects the job with "{error}"')
def step_api_rejects_job(context, error: str) -> None:
    assert context.create_response["statusCode"] == 400, context.create_response
    assert context.create_body == {"error": error}, context.create_body


@then('no job exists for the content hash of "{text}"')
def step_no_job_for_hash(context, text: str) -> None:
    item = context.hash_router.jobs_table.get_item(
        Key={"content_hash": _hash(text, "af_heart", "kokoro")}
    ).get("Item")
    assert item is None, item


@then("the job creation response carries no job token")
def step_no_job_token(context) -> None:
    assert context.create_response["statusCode"] == 201, context.create_response
    assert "job_token" not in context.create_body, context.create_body


@then("a caller with only the site key cannot claim that job")
def step_site_key_cannot_claim(context) -> None:
    content_hash = context.create_body["content_hash"]
    response = context.hash_router.call(
        "PUT",
        f"/jobs/{content_hash}/claim",
        headers={
            "x-auritus-site-key": SPEC_SITE_KEY,
            "authorization": f"Bearer {context.create_body.get('job_token', '')}",
        },
        body={"claim_owner": "local:site-key-caller"},
        path_parameters={"hash": content_hash},
    )
    assert response["statusCode"] == 403, response
    item = context.hash_router.jobs_table.get_item(Key={"content_hash": content_hash})[
        "Item"
    ]
    assert item["status"] == "pending", item


TOKEN_JOB_HASH = "token-revocation-spec-job"


@given('a "{status}" job whose worker token "{token}" was handed out earlier')
def step_job_with_handed_out_token(context, status: str, token: str) -> None:
    item = {
        "content_hash": TOKEN_JOB_HASH,
        "status": status,
        "text": "Token revocation narration.",
        "voice_id": "af_heart",
        "tts_backend": "kokoro",
        "site_id": f"site-{SPEC_SITE_KEY}",
        "job_token": token,
        "created_at": "2026-09-01T00:00:00Z",
    }
    if status == "claimed":
        item["claim_owner"] = "batch:spec-worker"
    if status == "done":
        item["audio_key"] = f"audio/{TOKEN_JOB_HASH}.wav"
    context.hash_router.jobs_table.put_item(Item=item)


def _call_with_token(context, method: str, route: str, token: str, body=None):
    context.token_response = context.hash_router.call(
        method,
        f"/jobs/{TOKEN_JOB_HASH}/{route}",
        headers={"authorization": f"Bearer {token}"},
        body=body,
        path_parameters={"hash": TOKEN_JOB_HASH},
    )


@when('the worker token "{token}" requests an audio upload URL for that job')
def step_token_presigns(context, token: str) -> None:
    _call_with_token(context, "POST", "presign-upload", token, body={})


@when('the worker token "{token}" marks that job done')
def step_token_marks_done(context, token: str) -> None:
    _call_with_token(
        context,
        "PUT",
        "done",
        token,
        body={
            "audio_key": f"audio/{TOKEN_JOB_HASH}.wav",
            "claim_owner": "batch:spec-worker",
        },
    )


@then("the API refuses the upload as forbidden")
def step_upload_forbidden(context) -> None:
    assert context.token_response["statusCode"] == 403, context.token_response


@then("the API returns an audio upload URL")
def step_upload_allowed(context) -> None:
    assert context.token_response["statusCode"] == 200, context.token_response
    assert "upload_url" in json.loads(context.token_response["body"])


@then("the finished job no longer holds a worker token")
def step_finished_job_has_no_token(context) -> None:
    assert context.token_response["statusCode"] == 200, context.token_response
    item = context.hash_router.jobs_table.get_item(
        Key={"content_hash": TOKEN_JOB_HASH}
    )["Item"]
    assert item["status"] == "done", item
    assert "job_token" not in item, item
