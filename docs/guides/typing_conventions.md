# Typing Conventions

`lx-data-models` is intended to provide strongly typed, standardized models for use across services. To keep runtime behavior and static typing aligned, use these rules consistently.

## Layer Roles

- Pydantic contract models define cross-service payloads and validation boundaries.
- Django ORM models define persistence and relations.
- Typed dicts and adapters handle storage or serialization details.

Do not use Django ORM models as transport contracts.

## Django ORM Rules

Pyright resolves dependencies from the repository's `.venv`, including
`django-stubs`. This prevents an unrelated active application environment from
producing false missing-symbol errors for Django's public APIs. Initialize the
environment and run the check with:

```bash
UV_PROJECT_ENVIRONMENT=.venv uv sync --extra dev --locked
UV_PROJECT_ENVIRONMENT=.venv uv run --locked pyright
```

CI uses the same `.venv` layout. `tests/test_django_typing.py` exercises valid
Django imports and rejects invalid field arguments and return-type assignments;
it runs the real checker without disabling diagnostics or substituting stubs.

- Always add `from __future__ import annotations` to Django model modules.
- Prefer string model references in relation fields.
- Keep relation field annotations safe for runtime import.
- Use `TYPE_CHECKING` imports only for static-only related model references.
- Avoid patterns that force Django field generics to evaluate at runtime without postponed annotations.
- If `django-stubs` cannot resolve a relation annotation but the runtime pattern
  is correct, use a narrow `# type: ignore[misc]` on the annotation rather than
  adding runtime imports solely for typing.

Recommended pattern:

```python
from __future__ import annotations

from typing import TYPE_CHECKING
from django.db import models

if TYPE_CHECKING:
    from .OtherModel import OtherModel


class Example(models.Model):
    related: models.ForeignKey["OtherModel", "OtherModel"] = models.ForeignKey(
        "OtherModel",
        on_delete=models.CASCADE,
    )
```

## Contract Rules

- Shared request and response payloads belong in `lx_dtypes.models.contracts`.
- Validate external payloads with `model_validate(...)`.
- Serialize contracts with `model_dump()`.
- Prefer enums over raw strings for stable domain values.
- Use `extra="forbid"` unless compatibility requires otherwise.

## Standardization Priorities

1. Make Django model imports runtime-safe.
2. Route cross-service payloads through contract models.
3. Replace repeated domain strings with enums or value objects.
4. Keep one typing style across `knowledge_base`, `ledger`, and `contracts`.
