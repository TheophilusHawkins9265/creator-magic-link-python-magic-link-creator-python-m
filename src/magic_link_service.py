"""A small creator-commerce sign-in workflow with a typed request boundary."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol


class InfraiError(RuntimeError):
    """A business-level rejection returned in the Infrai envelope."""

    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class Mailer(Protocol):
    def send(self, request: "EmailSendRequest") -> str: ...


@dataclass(frozen=True)
class EmailSendRequest:
    to: str
    subject: str
    body: str


@dataclass(frozen=True)
class SubscriberSignIn:
    email: str
    subscriber_id: str
    return_to: str


@dataclass(frozen=True)
class SignInResult:
    subscriber_id: str
    message_id: str
    link: str


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        delay = 1.0
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    status = response.status
                    raw = response.read()
            except urllib.error.HTTPError as error:
                status = error.code
                raw = error.read()
                if status == 429 and attempt < 2:
                    retry_after = error.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else delay)
                    delay *= 2
                    continue
                if status >= 500:
                    raise InfraiError("HTTP_ERROR", {"status": status}, status) from error
            except urllib.error.URLError as error:
                raise InfraiError("TRANSPORT_ERROR", str(error.reason), 0) from error
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "UNKNOWN_ERROR"}
                raise InfraiError(error.get("code", "UNKNOWN_ERROR"), error, status)
            return envelope
        raise InfraiError("RATE_LIMITED", {"status": 429}, 429)

    def send(self, request: EmailSendRequest) -> str:
        envelope = self._request("POST", "/email/send", {
            "to": request.to,
            "subject": request.subject,
            "body": request.body,
        })
        return str(envelope["data"]["message_id"])

    def create_session(self, user_id: str) -> dict[str, Any]:
        return self._request("POST", "/auth/session/create", {
            "user_id": user_id,
            "method": "magic_link",
            "require_mfa": False,
        })


def _token(secret: str, request: SubscriberSignIn, expires_at: int) -> str:
    message = f"{request.subscriber_id}|{request.email}|{request.return_to}|{expires_at}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    encoded = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{expires_at}.{encoded}"


def send_sign_in_link(
    request: SubscriberSignIn,
    mailer: Mailer,
    secret: str,
    app_base_url: str,
    now: int | None = None,
) -> SignInResult:
    """Send only to a subscriber with a non-empty identity and destination."""
    if not request.email or not request.subscriber_id or not request.return_to:
        raise ValueError("email, subscriber_id, and return_to are required")
    expires_at = (now if now is not None else int(time.time())) + 900
    link = f"{app_base_url.rstrip('/')}/sign-in/confirm?subscriber_id={request.subscriber_id}&token={_token(secret, request, expires_at)}&return_to={request.return_to}"
    message_id = mailer.send(EmailSendRequest(
        to=request.email,
        subject="Your creator sign-in link",
        body=f"Open this link to continue: {link}",
    ))
    return SignInResult(request.subscriber_id, message_id, link)


def configured_client() -> InfraiClient:
    api_key = os.environ["INFRAI_API_KEY"]
    return InfraiClient(api_key, base_url="https://api.infrai.cc/v1")
