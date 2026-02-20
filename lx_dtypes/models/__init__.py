from __future__ import annotations

from typing import Any

_EXPORTED = {
    "MODEL_NAMES",
    "ModelsDjangoLookupType",
    "ModelsLookupType",
    "models_django_lookup",
    "models_lookup",
    "MODEL_NAMES_LITERAL",
    "get_model_pk_field",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTED:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    # Lazy import to avoid importing Django model registry for pydantic-only use cases.
    from .main import (
        MODEL_NAMES,
        MODEL_NAMES_LITERAL,
        ModelsDjangoLookupType,
        ModelsLookupType,
        get_model_pk_field,
        models_django_lookup,
        models_lookup,
    )

    exports = {
        "MODEL_NAMES": MODEL_NAMES,
        "ModelsDjangoLookupType": ModelsDjangoLookupType,
        "ModelsLookupType": ModelsLookupType,
        "models_django_lookup": models_django_lookup,
        "models_lookup": models_lookup,
        "MODEL_NAMES_LITERAL": MODEL_NAMES_LITERAL,
        "get_model_pk_field": get_model_pk_field,
    }
    return exports[name]


__all__ = list(_EXPORTED)
