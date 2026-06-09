from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .main import api

__all__ = ["api"]


def __getattr__(name: str) -> Any:
    if name == "api":
        from .main import api

        return api
    raise AttributeError(name)
