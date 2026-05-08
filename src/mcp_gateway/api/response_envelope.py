from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ResponseEnvelope(BaseModel):
    code: str
    message: str
    data: Any = None
    traceId: str
    requestId: str


def success(data: Any, trace_id: str, request_id: str) -> ResponseEnvelope:
    return ResponseEnvelope(
        code="0",
        message="success",
        data=data,
        traceId=trace_id,
        requestId=request_id,
    )


def failure(code: str, message: str, trace_id: str, request_id: str) -> ResponseEnvelope:
    return ResponseEnvelope(
        code=code,
        message=message,
        data=None,
        traceId=trace_id,
        requestId=request_id,
    )
