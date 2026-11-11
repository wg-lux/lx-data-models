"""Ledger exports; load the Django-backed registry only when requested."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .main import (
        L_DDICTS,
        L_MODEL_NAMES_LITERAL,
        L_MODEL_NAMES_ORDERED,
        L_MODELS,
        L_MODELS_DJANGO,
        LedgerModelsDjangoLookupType,
        LedgerModelsLookupType,
        ledger_models_django_lookup,
        ledger_models_lookup,
    )


__all__ = [
    "L_DDICTS",
    "L_MODELS",
    "L_MODELS_DJANGO",
    "L_MODEL_NAMES_LITERAL",
    "L_MODEL_NAMES_ORDERED",
    "LedgerModelsDjangoLookupType",
    "LedgerModelsLookupType",
    "ledger_models_django_lookup",
    "ledger_models_lookup",
]


_PYDANTIC_EXPORTS = {
    "L_DDICTS",
    "L_MODELS",
    "ledger_models_lookup",
    "L_MODEL_NAMES_LITERAL",
    "L_MODEL_NAMES_ORDERED",
    "LedgerModelsLookupType",
}


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = "pydantic_main" if name in _PYDANTIC_EXPORTS else "main"
    value = getattr(import_module(f"{__name__}.{module}"), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
