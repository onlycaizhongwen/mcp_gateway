from __future__ import annotations

from uuid import uuid4


def ensure_trace_id(value: str | None = None) -> str:
    return value or f"trace-{uuid4().hex}"


def ensure_request_id(value: str | None = None) -> str:
    return value or f"req-{uuid4().hex}"
