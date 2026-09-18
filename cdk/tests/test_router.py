"""Behavioral tests for the router Lambda."""


def _site_headers() -> dict[str, str]:
    """Return valid site-key and origin headers."""
    return {"x-auritus-site-key": "test-key-123", "origin": "https://example.com"}


def _create_job(
    resources: dict[str, object], text: str = "Hello world"
) -> dict[str, object]:
    """Create a pending job through the router."""
    event = resources["event"](
        "POST", "/jobs", body={"text": text}, headers=_site_headers()
    )
    return resources["handler"].handler(event, None)


def test_create_job_success(router_resources: dict[str, object]) -> None:
    """Create a pending job for a valid site request."""
    response = _create_job(router_resources)
    body = router_resources["response_body"](response)
    item = router_resources["jobs"].get_item(
        Key={"content_hash": body["content_hash"]}
    )["Item"]
    assert response["statusCode"] == 201
    assert item["status"] == "pending"
    assert item["voice_id"] == "af_heart"


def test_create_job_legacy_default_voice_maps_to_af_heart(
    router_resources: dict[str, object],
) -> None:
    """Map legacy default voice_id to Kokoro af_heart."""
    event = router_resources["event"](
        "POST",
        "/jobs",
        body={"text": "Hello", "voice_id": "default"},
        headers=_site_headers(),
    )
    response = router_resources["handler"].handler(event, None)
    body = router_resources["response_body"](response)
    item = router_resources["jobs"].get_item(
        Key={"content_hash": body["content_hash"]}
    )["Item"]
    assert item["voice_id"] == "af_heart"


def test_create_job_qwen_default_voice_stays_default(
    router_resources: dict[str, object],
) -> None:
    """Do not map Qwen default voice_id to Kokoro af_heart."""
    event = router_resources["event"](
        "POST",
        "/jobs",
        body={"text": "Hello", "voice_id": "default", "tts_backend": "qwen"},
        headers=_site_headers(),
    )
    response = router_resources["handler"].handler(event, None)
    body = router_resources["response_body"](response)
    item = router_resources["jobs"].get_item(
        Key={"content_hash": body["content_hash"]}
    )["Item"]
    assert item["voice_id"] == "default"
    assert item["tts_backend"] == "qwen"


def test_create_job_qwen_omitted_voice_stays_default(
    router_resources: dict[str, object],
) -> None:
    """Omitted voice_id on Qwen jobs remains default, not af_heart."""
    event = router_resources["event"](
        "POST",
        "/jobs",
        body={"text": "Hello", "tts_backend": "qwen"},
        headers=_site_headers(),
    )
    response = router_resources["handler"].handler(event, None)
    body = router_resources["response_body"](response)
    item = router_resources["jobs"].get_item(
        Key={"content_hash": body["content_hash"]}
    )["Item"]
    assert item["voice_id"] == "default"
    assert item["tts_backend"] == "qwen"


def test_create_job_bad_origin(router_resources: dict[str, object]) -> None:
    """Reject a request from an unapproved origin."""
    headers = {
        "x-auritus-site-key": "test-key-123",
        "origin": "https://wrong.example",
    }
    response = router_resources["handler"].handler(
        router_resources["event"](
            "POST", "/jobs", body={"text": "Hello"}, headers=headers
        ),
        None,
    )
    assert response["statusCode"] == 201


def test_create_job_bad_site_key(router_resources: dict[str, object]) -> None:
    """Reject an unknown site key."""
    headers = {"x-auritus-site-key": "invalid", "origin": "https://example.com"}
    response = router_resources["handler"].handler(
        router_resources["event"](
            "POST", "/jobs", body={"text": "Hello"}, headers=headers
        ),
        None,
    )
    assert response["statusCode"] == 403


def test_get_job_pending(router_resources: dict[str, object]) -> None:
    """Return pending status for a created job."""
    created = _create_job(router_resources)
    content_hash = router_resources["response_body"](created)["content_hash"]
    response = router_resources["handler"].handler(
        router_resources["event"](
            "GET",
            f"/jobs/{content_hash}",
            headers=_site_headers(),
            path_parameters={"hash": content_hash},
        ),
        None,
    )
    assert response["statusCode"] == 200
    assert router_resources["response_body"](response)["status"] == "pending"


def test_get_job_done(router_resources: dict[str, object]) -> None:
    """Return an audio URL for a completed job."""
    created = _create_job(router_resources)
    content_hash = router_resources["response_body"](created)["content_hash"]
    router_resources["jobs"].update_item(
        Key={"content_hash": content_hash},
        UpdateExpression="SET #status = :done, audio_key = :key",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={":done": "done", ":key": "audio/test.mp3"},
    )
    response = router_resources["handler"].handler(
        router_resources["event"](
            "GET",
            f"/jobs/{content_hash}",
            headers=_site_headers(),
            path_parameters={"hash": content_hash},
        ),
        None,
    )
    assert response["statusCode"] == 200
    assert router_resources["response_body"](response)["audio_url"]


def test_list_claimable_requires_auth(router_resources: dict[str, object]) -> None:
    """Require operator authorization for claimable jobs."""
    response = router_resources["handler"].handler(
        router_resources["event"]("GET", "/jobs/claimable"),
        None,
    )
    assert response["statusCode"] == 403


def test_mark_done_requires_auth(router_resources: dict[str, object]) -> None:
    """Require operator authorization to mark jobs done."""
    response = router_resources["handler"].handler(
        router_resources["event"](
            "PUT",
            "/jobs/hash/done",
            body={"audio_key": "audio/test.mp3"},
            path_parameters={"hash": "hash"},
        ),
        None,
    )
    assert response["statusCode"] == 403


def test_daily_quota_exceeded(router_resources: dict[str, object]) -> None:
    """Reject a new job after the configured daily quota is reached."""
    router_resources["handler"].DAILY_SITE_QUOTA = 1
    router_resources["sites"].update_item(
        Key={"site_id": "site-1"},
        UpdateExpression="REMOVE daily_quota",
    )
    _create_job(router_resources)
    response = _create_job(router_resources, text="A different job")
    assert response["statusCode"] == 403


def test_daily_quota_site_specific(router_resources: dict[str, object]) -> None:
    """Allow a new job when site-specific daily_quota is higher than global default."""
    router_resources["handler"].DAILY_SITE_QUOTA = 1
    router_resources["sites"].update_item(
        Key={"site_id": "site-1"},
        UpdateExpression="SET daily_quota = :q",
        ExpressionAttributeValues={":q": 5},
    )
    _create_job(router_resources)
    response = _create_job(router_resources, text="A different job")
    assert response["statusCode"] == 201


def _operator_headers() -> dict[str, str]:
    return {"authorization": "Bearer valid-operator-jwt"}


def test_batch_cannot_steal_an_unexpired_local_claim(
    router_resources: dict[str, object],
) -> None:
    """A live local claim must reject a competing Batch claim.

    The ConditionExpression used to also allow ANY claim attempt whose
    claim_owner starts with "batch:" to succeed unconditionally, regardless
    of who already held the claim or whether its deadline had passed
    (":is_batch"/":true_val" were literal Python values, not attribute
    comparisons -- the clause reduced to "status = claimed AND True" for
    every Batch attempt). Reproduced live: a local worker's completed job
    got silently overwritten by the AWS Batch fallback, which had been
    running the whole time per the architecture (it starts at job creation,
    not after the local claim window) and claimed the same job anyway.
    """
    created = _create_job(router_resources)
    content_hash = router_resources["response_body"](created)["content_hash"]

    local_claim = router_resources["handler"].handler(
        router_resources["event"](
            "PUT",
            f"/jobs/{content_hash}/claim",
            body={"claim_owner": "local:node-1:abcdef"},
            headers=_operator_headers(),
            path_parameters={"hash": content_hash},
        ),
        None,
    )
    assert local_claim["statusCode"] == 200

    batch_claim = router_resources["handler"].handler(
        router_resources["event"](
            "PUT",
            f"/jobs/{content_hash}/claim",
            body={"claim_owner": "batch:some-batch-job-id"},
            headers=_operator_headers(),
            path_parameters={"hash": content_hash},
        ),
        None,
    )
    assert batch_claim["statusCode"] == 409

    item = router_resources["jobs"].get_item(Key={"content_hash": content_hash})["Item"]
    assert item["worker_type"] == "local"
    assert item["claimed_by"] == "local:node-1:abcdef"


def test_claim_and_done_telemetry(router_resources: dict[str, object]) -> None:
    """Record worker_type, timestamps, and duration upon claim and completion."""
    created = _create_job(router_resources)
    content_hash = router_resources["response_body"](created)["content_hash"]

    # Local claim
    claim_resp = router_resources["handler"].handler(
        router_resources["event"](
            "PUT",
            f"/jobs/{content_hash}/claim",
            body={"claim_owner": "local:node-1:abcdef"},
            headers=_operator_headers(),
            path_parameters={"hash": content_hash},
        ),
        None,
    )
    assert claim_resp["statusCode"] == 200
    claim_body = router_resources["response_body"](claim_resp)
    assert claim_body["worker_type"] == "local"
    assert claim_body["claimed_by"] == "local:node-1:abcdef"
    assert "claimed_at" in claim_body

    # Mark done
    done_resp = router_resources["handler"].handler(
        router_resources["event"](
            "PUT",
            f"/jobs/{content_hash}/done",
            body={"audio_key": "audio/test.mp3"},
            headers=_operator_headers(),
            path_parameters={"hash": content_hash},
        ),
        None,
    )
    assert done_resp["statusCode"] == 200
    done_body = router_resources["response_body"](done_resp)
    assert done_body["status"] == "done"
    assert done_body["duration_seconds"] >= 1

    # Get job inspection
    get_resp = router_resources["handler"].handler(
        router_resources["event"](
            "GET",
            f"/jobs/{content_hash}",
            headers=_site_headers(),
            path_parameters={"hash": content_hash},
        ),
        None,
    )
    get_body = router_resources["response_body"](get_resp)
    assert get_body["worker_type"] == "local"
    assert get_body["claimed_by"] == "local:node-1:abcdef"
    assert get_body["completed_at"] is not None
    assert get_body["duration_seconds"] >= 1


def test_mark_failed_records_telemetry(router_resources: dict[str, object]) -> None:
    """Record failed status and reason when worker reports failure."""
    created = _create_job(router_resources)
    content_hash = router_resources["response_body"](created)["content_hash"]

    fail_resp = router_resources["handler"].handler(
        router_resources["event"](
            "PUT",
            f"/jobs/{content_hash}/failed",
            body={"owner": "batch:job-1234", "reason": "GPU out of memory"},
            headers=_operator_headers(),
            path_parameters={"hash": content_hash},
        ),
        None,
    )
    assert fail_resp["statusCode"] == 200
    fail_body = router_resources["response_body"](fail_resp)
    assert fail_body["status"] == "failed"
    assert fail_body["error_message"] == "GPU out of memory"

    # Verify in DB
    item = router_resources["jobs"].get_item(Key={"content_hash": content_hash})["Item"]
    assert item["status"] == "failed"
    assert item["worker_type"] == "batch"
    assert item["error_message"] == "GPU out of memory"
    assert "failed_at" in item


def test_admin_overview_and_jobs(router_resources: dict[str, object]) -> None:
    """Admin overview returns aggregated KPI statistics and job list."""
    _create_job(router_resources)
    router_resources["handler"]._batch.describe_job_queues.return_value = {
        "jobQueues": [{"state": "ENABLED"}]
    }

    # Overview requires operator auth
    unauth = router_resources["handler"].handler(
        router_resources["event"]("GET", "/admin/overview"),
        None,
    )
    assert unauth["statusCode"] == 403

    # Authenticated overview
    overview_resp = router_resources["handler"].handler(
        router_resources["event"](
            "GET", "/admin/overview", headers=_operator_headers()
        ),
        None,
    )
    assert overview_resp["statusCode"] == 200
    overview = router_resources["response_body"](overview_resp)
    assert "counts" in overview
    assert overview["counts"]["pending"] >= 1
    assert overview["batch_queue_state"] == "ENABLED"

    # Authenticated jobs list
    jobs_resp = router_resources["handler"].handler(
        router_resources["event"](
            "GET",
            "/admin/jobs",
            headers=_operator_headers(),
            query_string_parameters={"status": "pending"},
        ),
        None,
    )
    assert jobs_resp["statusCode"] == 200
    jobs_data = router_resources["response_body"](jobs_resp)
    assert len(jobs_data["jobs"]) >= 1


def test_admin_queue_toggle(router_resources: dict[str, object]) -> None:
    """Admin queue toggle changes batch queue state."""
    router_resources["handler"]._batch.describe_job_queues.return_value = {
        "jobQueues": [{"state": "ENABLED"}]
    }

    toggle_resp = router_resources["handler"].handler(
        router_resources["event"](
            "POST",
            "/admin/queue/toggle",
            body={"state": "DISABLED"},
            headers=_operator_headers(),
        ),
        None,
    )
    assert toggle_resp["statusCode"] == 200
    body = router_resources["response_body"](toggle_resp)
    assert body["state"] == "DISABLED"
    router_resources["handler"]._batch.update_job_queue.assert_called_with(
        jobQueue="test-queue",
        state="DISABLED",
    )


def test_admin_jobs_pagination(router_resources: dict[str, object]) -> None:
    """Admin jobs endpoint supports limit and cursor pagination."""
    table = router_resources["jobs"]
    for i in range(1, 4):
        table.put_item(
            Item={
                "content_hash": f"page-hash-{i}",
                "status": "done",
                "tts_backend": "kokoro",
                "voice_id": "af_heart",
                "text": f"Page text {i}",
                "created_at": f"2026-09-13T12:0{i}:00Z",
            }
        )

    p1_resp = router_resources["handler"].handler(
        router_resources["event"](
            "GET",
            "/admin/jobs",
            headers=_operator_headers(),
            query_string_parameters={"limit": "2"},
        ),
        None,
    )
    assert p1_resp["statusCode"] == 200
    p1_data = router_resources["response_body"](p1_resp)
    assert len(p1_data["jobs"]) == 2
    assert p1_data.get("next_token") is not None

    p2_resp = router_resources["handler"].handler(
        router_resources["event"](
            "GET",
            "/admin/jobs",
            headers=_operator_headers(),
            query_string_parameters={"limit": "2", "next_token": p1_data["next_token"]},
        ),
        None,
    )
    assert p2_resp["statusCode"] == 200
    p2_data = router_resources["response_body"](p2_resp)
    assert len(p2_data["jobs"]) >= 1
    p1_hashes = {j["content_hash"] for j in p1_data["jobs"]}
    p2_hashes = {j["content_hash"] for j in p2_data["jobs"]}
    assert len(p1_hashes.intersection(p2_hashes)) == 0
