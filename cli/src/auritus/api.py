"""Typed HTTP client for the Auritus backend API."""

from __future__ import annotations

from typing import Any

import httpx

from auritus.auth import (
    AuthError,
    RefreshExpiredError,
    get_access_token,
    refresh_tokens,
)
from auritus.config import load_config


class AuritusApiError(RuntimeError):
    """Raised when the Auritus API returns an error."""


class AuritusSessionExpiredError(AuritusApiError):
    """Raised when the operator refresh token is dead and re-login is required."""


class AuritusClient:
    """HTTP client for Auritus operator and site-management routes."""

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        """Create a client.

        :param base_url: API base URL; defaults to config api_endpoint.
        :param token: Bearer token; defaults to cached Cognito access token.
        """
        cfg = load_config()
        self.base_url = (base_url or cfg.get("api_endpoint") or "").rstrip("/")
        if not self.base_url:
            raise AuritusApiError(
                "api_endpoint is not set. Run `auritus deploy` or `auritus config set`."
            )
        self._token = token

    def _headers(self, site_key: str | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if site_key:
            headers["X-Auritus-Site-Key"] = site_key
        else:
            try:
                token = self._token or get_access_token()
            except RefreshExpiredError as exc:
                raise AuritusSessionExpiredError(
                    "Session expired. Run `auritus login`."
                ) from exc
            except AuthError as exc:
                raise AuritusApiError(str(exc)) from exc
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _send(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json_body: dict[str, Any] | None,
    ) -> httpx.Response:
        return httpx.request(
            method,
            url,
            headers=headers,
            json=json_body,
            timeout=60.0,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        site_key: str | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = self._send(
            method, url, headers=self._headers(site_key=site_key), json_body=json_body
        )
        if response.status_code == 401 and not site_key:
            try:
                refresh_tokens()
            except RefreshExpiredError as exc:
                raise AuritusSessionExpiredError(
                    "Session expired. Run `auritus login`."
                ) from exc
            except AuthError as exc:
                raise AuritusApiError(str(exc)) from exc
            response = self._send(
                method,
                url,
                headers=self._headers(site_key=site_key),
                json_body=json_body,
            )
        if response.status_code >= 400:
            raise AuritusApiError(
                f"{method} {path} failed: {response.status_code} {response.text}"
            )
        if not response.content:
            return {}
        return response.json()

    def create_job(
        self,
        *,
        content_hash: str,
        text: str,
        site_key: str,
        name: str = "",
        byline: str = "",
        tts_backend: str = "kokoro",
        voice_id: str = "default",
    ) -> dict[str, Any]:
        """Create a generation job."""
        return self._request(
            "POST",
            "/jobs",
            json_body={
                "content_hash": content_hash,
                "text": text,
                "name": name,
                "byline": byline,
                "tts_backend": tts_backend,
                "voice_id": voice_id,
            },
            site_key=site_key,
        )

    def get_job(self, content_hash: str, *, site_key: str) -> dict[str, Any]:
        """Fetch job status and metadata."""
        return self._request("GET", f"/jobs/{content_hash}", site_key=site_key)

    def list_claimable(self) -> list[dict[str, Any]]:
        """List jobs available for the local worker to claim."""
        data = self._request("GET", "/jobs/claimable")
        return list(data.get("jobs") or [])

    def claim_job(self, content_hash: str, owner: str) -> dict[str, Any]:
        """Attempt a mutex claim on a job."""
        return self._request(
            "PUT",
            f"/jobs/{content_hash}/claim",
            json_body={"claim_owner": owner},
        )

    def renew_claim(self, content_hash: str, owner: str) -> dict[str, Any]:
        """Renew an in-flight claim (heartbeat) for long-running generation."""
        return self._request(
            "PUT",
            f"/jobs/{content_hash}/claim",
            json_body={"claim_owner": owner, "renew": True},
        )

    def mark_done(
        self, content_hash: str, *, audio_key: str, owner: str
    ) -> dict[str, Any]:
        """Mark a job done after audio upload."""
        return self._request(
            "PUT",
            f"/jobs/{content_hash}/done",
            json_body={"audio_key": audio_key, "owner": owner},
        )

    def complete_job(
        self, content_hash: str, *, audio_key: str, owner: str
    ) -> dict[str, Any]:
        """Mark a job done after audio upload (alias for :meth:`mark_done`)."""
        return self.mark_done(content_hash, audio_key=audio_key, owner=owner)

    def create_site(self, *, origin: str, name: str = "") -> dict[str, Any]:
        """Mint a site key for an embed origin."""
        return self._request(
            "POST",
            "/sites",
            json_body={"origin": origin, "name": name},
        )

    def list_sites(self) -> list[dict[str, Any]]:
        """List site keys for the operator."""
        data = self._request("GET", "/sites")
        return list(data.get("sites") or [])

    def revoke_site(self, site_id: str) -> dict[str, Any]:
        """Revoke a site key."""
        return self._request("DELETE", f"/sites/{site_id}")

    def delete_job(self, content_hash: str) -> dict[str, Any]:
        """Delete a generated audio job and its audio artifact.

        :param content_hash: The content hash identifying the job.
        :returns: The API response confirming deletion.
        """
        return self._request("DELETE", f"/admin/jobs/{content_hash}")

    def regenerate_job(self, content_hash: str) -> dict[str, Any]:
        """Force regeneration of a job, resetting it to pending in place.

        :param content_hash: The content hash identifying the job.
        :returns: The API response with the job reset to pending.
        """
        return self._request(
            "POST", f"/admin/jobs/{content_hash}/regenerate", json_body={}
        )

    def disable_batch_queue(self) -> dict[str, Any]:
        """Emergency kill-switch: disable the Batch job queue."""
        return self._request(
            "POST", "/admin/killswitch", json_body={"action": "disable"}
        )

    def enable_batch_queue(self) -> dict[str, Any]:
        """Re-enable the Batch job queue after a kill-switch."""
        return self._request(
            "POST", "/admin/killswitch", json_body={"action": "enable"}
        )

    def presign_upload(self, content_hash: str) -> dict[str, Any]:
        """Obtain a presigned S3 upload URL for generated audio."""
        return self._request(
            "POST",
            f"/jobs/{content_hash}/presign-upload",
            json_body={},
        )
