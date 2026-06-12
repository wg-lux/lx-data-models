from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


PermissionMode = Literal["default", "force_auth", "force_public"]


class DynamicPermissionConfigPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    mode: PermissionMode = "default"


__all__ = ["DynamicPermissionConfigPayload", "PermissionMode"]
