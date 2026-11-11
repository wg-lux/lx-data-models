from __future__ import annotations

from typing import Literal

from lx_dtypes.models.model import FrozenContractModel

PermissionMode = Literal["default", "force_auth", "force_public"]


class DynamicPermissionConfigPayload(FrozenContractModel):
    mode: PermissionMode = "default"


__all__ = ["DynamicPermissionConfigPayload", "PermissionMode"]
