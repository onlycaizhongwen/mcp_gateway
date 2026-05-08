from __future__ import annotations

from pydantic import BaseModel


class AuthContext(BaseModel):
    tenant_id: str | None = None
    app_id: str | None = None
    user: dict | None = None
