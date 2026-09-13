"""Behave steps for CLI Cognito login scenarios."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from behave import given, then, when
from botocore.exceptions import ClientError

from auritus.auth import (
    RefreshExpiredError,
    clear_tokens,
    credentials_path,
    get_access_token,
    load_tokens,
    login_with_password,
    maybe_warn_near_expiry,
    notify_session_state,
    refresh_tokens,
    revoke_tokens,
    save_tokens,
)


@given("a mock Cognito USER_PASSWORD_AUTH endpoint")
def step_mock_initiate_auth(context) -> None:
    context.mock_username = "operator@example.com"
    context.mock_password = "placeholder-password"
    context.mock_auth_result = {
        "AuthenticationResult": {
            "AccessToken": "mock-access",
            "RefreshToken": "mock-refresh",
            "ExpiresIn": 3600,
            "TokenType": "Bearer",
        }
    }
    clear_tokens()


@when("the operator logs in with email and password")
def step_password_login(context) -> None:
    mock_client = MagicMock()
    mock_client.initiate_auth.return_value = context.mock_auth_result

    mock_config = {
        "cognito_client_id": "test-client",
        "region": "us-east-1",
    }

    with patch("auritus.auth.boto3.client", return_value=mock_client), patch(
        "auritus.auth.load_config", return_value=mock_config
    ):
        login_with_password(context.mock_username, context.mock_password)


@then("Cognito tokens are cached for the CLI")
def step_tokens_cached(context) -> None:
    path = credentials_path()
    assert path.is_file()
    assert (path.stat().st_mode & 0o777) == 0o600
    cached = load_tokens()
    assert cached is not None
    assert cached.get("access_token") == "mock-access"
    assert cached.get("refresh_token") == "mock-refresh"
    assert cached.get("obtained_at") is not None


@given("cached Cognito tokens that are near expiry")
def step_near_expiry(context) -> None:
    save_tokens(
        {
            "access_token": "old-access",
            "refresh_token": "mock-refresh",
            "obtained_at": 1,
            "expires_in": 3600,
            "token_type": "Bearer",
        }
    )


@when("the CLI refreshes credentials")
def step_refresh(context) -> None:
    refreshed = {
        "access_token": "new-access",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    def fake_post(url, data=None, **kwargs):
        class Response:
            status_code = 200

            def json(self):
                return refreshed

            def raise_for_status(self):
                return None

        return Response()

    mock_config = {
        "cognito_client_id": "test-client",
        "cognito_domain": "auritus-test",
        "region": "us-east-1",
    }
    with patch("auritus.auth.httpx.post", side_effect=fake_post), patch(
        "auritus.auth.load_config", return_value=mock_config
    ):
        token = get_access_token()
    context.refreshed_access = token


@then("a new access token is available")
def step_new_token(context) -> None:
    assert context.refreshed_access == "new-access"
    cached = load_tokens()
    assert cached is not None
    assert cached.get("access_token") == "new-access"


@given("cached Cognito tokens with a refresh token")
def step_cached_refresh(context) -> None:
    save_tokens(
        {
            "access_token": "old-access",
            "refresh_token": "mock-refresh",
            "id_token": _id_token_with_email("operator@example.com"),
            "obtained_at": 1,
            "expires_in": 3600,
            "refresh_obtained_at": 1,
            "token_type": "Bearer",
        }
    )


@given("cached Cognito tokens")
def step_cached_tokens(context) -> None:
    save_tokens(
        {
            "access_token": "old-access",
            "refresh_token": "mock-refresh",
            "id_token": _id_token_with_email("operator@example.com"),
            "obtained_at": 1,
            "expires_in": 3600,
            "refresh_obtained_at": 1,
            "token_type": "Bearer",
        }
    )


def _id_token_with_email(email: str) -> str:
    import base64

    header = base64.urlsafe_b64encode(b'{"alg":"RS256"}').rstrip(b"=").decode()
    payload = (
        base64.urlsafe_b64encode(f'{{"email":"{email}"}}'.encode())
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{payload}.sig"


@when("Cognito rejects the refresh with invalid_grant")
def step_reject_refresh(context) -> None:
    def fake_post(url, data=None, **kwargs):
        class Response:
            status_code = 400

            def json(self):
                return {"error": "invalid_grant"}

            def text(self):
                return '{"error":"invalid_grant"}'

        return Response()

    mock_config = {
        "cognito_client_id": "test-client",
        "cognito_domain": "auritus-test",
        "region": "us-east-1",
    }
    context.refresh_exc = None
    with patch("auritus.auth.httpx.post", side_effect=fake_post), patch(
        "auritus.auth.load_config", return_value=mock_config
    ):
        try:
            refresh_tokens()
        except RefreshExpiredError as exc:
            context.refresh_exc = exc


@then("refresh_tokens raises RefreshExpiredError")
def step_refresh_expired(context) -> None:
    assert isinstance(context.refresh_exc, RefreshExpiredError)


@given("cached Cognito tokens with a valid refresh token")
def step_cached_valid_refresh(context) -> None:
    save_tokens(
        {
            "access_token": "old-access",
            "refresh_token": "mock-refresh",
            "id_token": _id_token_with_email("operator@example.com"),
            "obtained_at": 1,
            "expires_in": 3600,
            "refresh_obtained_at": 1,
            "token_type": "Bearer",
        }
    )


@when("the API client receives a 401 on the first call")
def step_api_401(context) -> None:
    from auritus.api import AuritusClient

    refreshed = {
        "access_token": "new-access",
        "expires_in": 3600,
        "token_type": "Bearer",
    }
    calls = {"count": 0}

    def fake_request(method, url, **kwargs):
        calls["count"] += 1
        status = 401 if calls["count"] == 1 else 200

        class Response:
            status_code = status
            content = b'{"ok": true}' if status == 200 else b'{"error":"unauth"}'
            text = '{"ok": true}' if status == 200 else '{"error":"unauth"}'

            def json(self):
                return {"ok": True} if status == 200 else {"error": "unauth"}

        return Response()

    def fake_post(url, data=None, **kwargs):
        class Response:
            status_code = 200

            def json(self):
                return refreshed

        return Response()

    mock_config = {
        "api_endpoint": "https://api.test",
        "cognito_client_id": "test-client",
        "cognito_domain": "auritus-test",
        "region": "us-east-1",
    }
    with patch("auritus.api.httpx.request", side_effect=fake_request), patch(
        "auritus.auth.httpx.post", side_effect=fake_post
    ), patch("auritus.auth.load_config", return_value=mock_config), patch(
        "auritus.api.load_config", return_value=mock_config
    ):
        client = AuritusClient()
        context.api_result = client.list_claimable()
    context.api_calls = calls["count"]


@then("it refreshes and retries the call once")
def step_retried_once(context) -> None:
    assert context.api_calls == 2
    assert context.api_result == []


@when("the operator runs auritus logout")
def step_run_logout(context) -> None:
    context.revoke_calls = []

    def fake_post(url, data=None, **kwargs):
        context.revoke_calls.append({"url": url, "data": data})

        class Response:
            status_code = 200

        return Response()

    mock_config = {
        "cognito_client_id": "test-client",
        "cognito_domain": "auritus-test",
        "region": "us-east-1",
    }
    with patch("auritus.auth.httpx.post", side_effect=fake_post), patch(
        "auritus.auth.load_config", return_value=mock_config
    ):
        revoke_tokens()


@then("the refresh token is revoked at Cognito")
def step_revoked(context) -> None:
    assert context.revoke_calls, "no revoke call was made"
    assert "/oauth2/revoke" in context.revoke_calls[0]["url"]
    assert context.revoke_calls[0]["data"]["token"] == "mock-refresh"


@then("local credentials are cleared")
def step_creds_cleared(context) -> None:
    assert not credentials_path().exists()


@given("cached Cognito tokens whose refresh token expires in 24 hours")
def step_near_refresh_expiry(context) -> None:
    import time as _time

    now = int(_time.time())
    save_tokens(
        {
            "access_token": "old-access",
            "refresh_token": "mock-refresh",
            "id_token": _id_token_with_email("operator@example.com"),
            "obtained_at": now,
            "expires_in": 3600,
            "refresh_obtained_at": now - (30 * 24 * 60 * 60) + (24 * 60 * 60),
            "token_type": "Bearer",
        }
    )


@when("the worker checks session state")
def step_worker_checks(context) -> None:
    context.warn_posts = []

    def fake_post(url, data=None, json=None, **kwargs):
        context.warn_posts.append({"url": url, "json": json, "data": data})

        class Response:
            status_code = 200

        return Response()

    mock_config = {
        "api_endpoint": "https://api.test",
        "cognito_client_id": "test-client",
        "cognito_domain": "auritus-test",
        "region": "us-east-1",
    }
    with patch("auritus.auth.httpx.post", side_effect=fake_post), patch(
        "auritus.auth.load_config", return_value=mock_config
    ):
        context.warned = maybe_warn_near_expiry("local:test-host:abc")


@then("a warning alert is posted to /alerts/session")
def step_warning_posted(context) -> None:
    assert context.warned is True
    assert context.warn_posts, "no alert posted"
    assert context.warn_posts[0]["url"].endswith("/alerts/session")
    assert context.warn_posts[0]["json"]["kind"] == "warning"


@then("the warning is throttled to once per day")
def step_warning_throttled(context) -> None:
    import time as _time

    mock_config = {
        "api_endpoint": "https://api.test",
        "cognito_client_id": "test-client",
        "cognito_domain": "auritus-test",
        "region": "us-east-1",
    }
    second_posts = []
    with patch(
        "auritus.auth.httpx.post",
        side_effect=lambda *a, **k: second_posts.append(1)
        or type("R", (), {"status_code": 200})(),
    ), patch("auritus.auth.load_config", return_value=mock_config):
        again = maybe_warn_near_expiry("local:test-host:abc")
    assert again is False
    assert second_posts == []


@given("cached Cognito tokens with a revoked refresh token")
def step_revoked_refresh(context) -> None:
    save_tokens(
        {
            "access_token": "old-access",
            "refresh_token": "mock-refresh",
            "id_token": _id_token_with_email("operator@example.com"),
            "obtained_at": 1,
            "expires_in": 3600,
            "refresh_obtained_at": 1,
            "token_type": "Bearer",
        }
    )


@when("the worker fails to refresh")
def step_worker_fails_refresh(context) -> None:
    from auritus.worker.daemon import run_worker

    def fake_request(method, url, **kwargs):
        class Response:
            status_code = 401
            content = b'{"error":"unauth"}'
            text = '{"error":"unauth"}'

            def json(self):
                return {"error": "unauth"}

        return Response()

    def fake_post(url, data=None, **kwargs):
        class Response:
            status_code = 400

            def json(self):
                return {"error": "invalid_grant"}

            def text(self):
                return '{"error":"invalid_grant"}'

        return Response()

    mock_config = {
        "api_endpoint": "https://api.test",
        "cognito_client_id": "test-client",
        "cognito_domain": "auritus-test",
        "region": "us-east-1",
        "worker": {
            "claim_timeout": 900,
            "poll_interval": 5,
            "tts_backend": "higgs",
        },
    }
    context.exit_code = 0
    context.expired_posts = []
    with patch("auritus.api.httpx.request", side_effect=fake_request), patch(
        "auritus.auth.httpx.post", side_effect=fake_post
    ), patch("auritus.auth.load_config", return_value=mock_config), patch(
        "auritus.api.load_config", return_value=mock_config
    ), patch(
        "auritus.worker.daemon.load_config", return_value=mock_config
    ), patch(
        "auritus.worker.daemon.notify_session_state",
        side_effect=lambda kind, machine: context.expired_posts.append(
            {"kind": kind, "machine": machine}
        ),
    ), patch(
        "auritus.worker.daemon.maybe_warn_near_expiry", return_value=False
    ), patch(
        "auritus.worker.daemon.AuritusClient"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client.list_claimable.side_effect = _raise_session_expired
        mock_client_cls.return_value = mock_client
        try:
            run_worker(once=True)
        except SystemExit as exc:
            context.exit_code = int(exc.code or 0)


def _raise_session_expired(*a, **k):
    from auritus.api import AuritusSessionExpiredError

    raise AuritusSessionExpiredError("Session expired. Run `auritus login`.")


@then("an expired alert is posted to /alerts/session")
def step_expired_posted(context) -> None:
    assert context.expired_posts, "no expired alert posted"
    assert context.expired_posts[0]["kind"] == "expired"


@then("the worker exits with code 2")
def step_worker_exit_code(context) -> None:
    assert context.exit_code == 2


@given("the alert endpoint and a known Cognito operator")
def step_alert_endpoint(context) -> None:
    import importlib.util
    from pathlib import Path

    handler_path = (
        Path(__file__).resolve().parents[2]
        / "cdk"
        / "lambdas"
        / "router"
        / "handler.py"
    )
    import os as _os

    _os.environ.setdefault("JOBS_TABLE", "test-jobs")
    _os.environ.setdefault("SITES_TABLE", "test-sites")
    _os.environ.setdefault("AUDIO_BUCKET", "test-audio")
    spec = importlib.util.spec_from_file_location(
        "auritus_router_handler_under_test", handler_path
    )
    assert spec and spec.loader
    context.handler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(context.handler)
    context.known_email = "operator@example.com"
    context.unknown_email = "nobody@example.com"
    context.sent_emails = []

    def fake_admin_get_user(UserPoolId, Username):
        if Username == context.known_email:
            return {"Username": Username}
        raise ClientError(
            {"Error": {"Code": "UserNotFoundException", "Message": "not found"}},
            "AdminGetUser",
        )

    def fake_send_email(Source, Destination, Message):
        context.sent_emails.append(
            {"to": Destination["ToAddresses"], "subject": Message["Subject"]["Data"]}
        )
        return {"MessageId": "test"}

    class FakeTable:
        def __init__(self):
            self.items = {}

        def put_item(self, Item, ConditionExpression=None):
            key = Item["content_hash"]
            if key in self.items:
                raise ClientError(
                    {
                        "Error": {
                            "Code": "ConditionalCheckFailedException",
                            "Message": "exists",
                        }
                    },
                    "PutItem",
                )
            self.items[key] = Item
            return {}

    context.fake_table = FakeTable()
    context._patches = [
        patch.object(context.handler, "USER_POOL_ID", "pool-id"),
        patch.object(context.handler, "SES_FROM_ADDRESS", "auritus@aurit.us"),
        patch.object(context.handler, "_cognito"),
        patch.object(context.handler, "_ses"),
        patch.object(context.handler, "_jobs", context.fake_table),
    ]
    for p in context._patches:
        p.start()
    context.handler._cognito.admin_get_user.side_effect = fake_admin_get_user
    context.handler._ses.send_email.side_effect = fake_send_email
    context.add_cleanup(lambda: [p.stop() for p in context._patches])


@when("an alert is posted for an unknown email")
def step_post_unknown(context) -> None:
    context.resp_unknown = context.handler._alert_session(
        {"operator_email": context.unknown_email, "kind": "expired", "machine": "m"}
    )


@then("no email is sent and the response is 404")
def step_no_email_404(context) -> None:
    assert context.resp_unknown["statusCode"] == 404
    assert context.sent_emails == []


@when("a second warning alert is posted within 6 hours")
def step_post_second(context) -> None:
    context.resp_first = context.handler._alert_session(
        {
            "operator_email": context.known_email,
            "kind": "warning",
            "machine": "m",
        }
    )
    context.resp_second = context.handler._alert_session(
        {
            "operator_email": context.known_email,
            "kind": "warning",
            "machine": "m",
        }
    )


@then("the response is 429 and no second email is sent")
def step_429(context) -> None:
    assert context.resp_first["statusCode"] == 200
    assert context.resp_second["statusCode"] == 429
    assert len(context.sent_emails) == 1
