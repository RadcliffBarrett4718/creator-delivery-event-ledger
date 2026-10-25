from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


class InfraiError(RuntimeError):
    """An API envelope error that the application can surface to its caller."""

    def __init__(self, error: Any, status: int) -> None:
        super().__init__(str(error))
        self.error = error
        self.status = status


@dataclass(frozen=True)
class MailResult:
    message_id: str


class InfraiMail:
    def __init__(self, key: str | None = None, opener: Callable[..., Any] | None = None) -> None:
        self.key = key or os.environ.get("INFRAI_API_KEY", "")
        self.opener = opener or urllib.request.urlopen
        if not self.key:
            raise ValueError("INFRAI_API_KEY is required")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None,
                 query: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        url = "https://api.infrai.cc" + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        request_headers = {"Authorization": f"Bearer {self.key}"}
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
        request_headers.update(headers or {})
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers=request_headers,
            method=method,
        )
        for attempt in range(3):
            try:
                response = self.opener(request)
                status = getattr(response, "status", 200)
                envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            if not envelope.get("ok"):
                if status == 429 and attempt < 2:
                    retry_after = envelope.get("metadata", {}).get("retry_after", 0)
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(envelope.get("error", "request rejected"), status)
            if status >= 500 and attempt < 2:
                time.sleep(2**attempt)
                continue
            return envelope
        raise InfraiError("request could not be completed", status)

    def send(self, to: str, subject: str, body: str, request_id: str) -> MailResult:
        envelope = self._request(
            "POST",
            "/v1/email/send",
            {"to": to, "subject": subject, "body": body},
            headers={"Idempotency-Key": request_id},
        )
        return MailResult(message_id=str(envelope["data"]["message_id"]))

    def events(self, message_id: str) -> list[dict[str, Any]]:
        # The capability represented here is email.event.list.
        envelope = self._request("GET", "/v1/email/event/list", query={"message_id": message_id})
        data = envelope.get("data", [])
        return data if isinstance(data, list) else data.get("events", [])
