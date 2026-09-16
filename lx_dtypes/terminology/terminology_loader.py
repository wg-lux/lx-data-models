"""One configured terminology service for all application routes."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from platformdirs import user_data_path

from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.terminology.terminology_service import (
    TerminologyError,
    TerminologyService,
)


def _terminology_root(path: str | Path | None = None) -> Path:
    """Explicit argument > Django setting > per-user standalone storage.

    Missing/None means use the default. Invalid explicit values remain errors.
    This function resolves a location; it does not create or hydrate it.
    """
    configured: object = path

    # Honour a selected but not-yet-evaluated Django settings module too.
    # A standalone Python caller need not configure Django just for this path.
    if configured is None and (
        settings.configured or os.environ.get("DJANGO_SETTINGS_MODULE")
    ):
        configured = getattr(settings, "TERMINOLOGY_ROOT", None)

    if configured is None:
        configured = (
            user_data_path("lx-dtypes", appauthor=False, ensure_exists=False)
            / "terminology"
        )

    if not isinstance(configured, (str, Path)) or not str(configured).strip():
        raise ImproperlyConfigured(
            f"TERMINOLOGY_ROOT must be an absolute path or None; got {configured!r}"
        )

    root = Path(configured)
    if not root.is_absolute():
        raise ImproperlyConfigured(
            f"TERMINOLOGY_ROOT must be an absolute path; got {configured!r}"
        )

    return root.resolve()


def hydrate_shipped_terminology(path: str | Path | None = None) -> Path:
    """Seed the configured registry from lx_dtypes/data, preserving existing edits."""
    service = TerminologyService(
        registry_path=_terminology_root(path) / "registry.json",
    )
    service.provision()
    return service.registry_path


@lru_cache(maxsize=1)
def get_terminology_service() -> TerminologyService:
    """Construct the service without reading or provisioning its registry.

    Safe to call while registering routes. Run hydrate_shipped_terminology()
    explicitly during deployment or in a test fixture that needs editable data.
    """
    return TerminologyService(
        registry_path=_terminology_root() / "registry.json",
    )


def active_kb_identity() -> tuple[str, str]:
    identity = get_terminology_service().active_identity()
    if identity is None:
        raise TerminologyError(409, "No active knowledge-base bundle is selected.")
    return identity


def load_module_kb(module_name: str, *, version: str | None = None) -> KnowledgeBase:
    module_name = module_name.strip()
    if not module_name:
        raise TerminologyError(409, "A knowledge-base module name is required.")
    if version is None:
        active_module, active_version = active_kb_identity()
        if module_name != active_module:
            raise TerminologyError(
                409,
                "An explicit version is required for a non-active module.",
            )
        version = active_version
    else:
        version = version.strip()
        if not version:
            raise TerminologyError(409, "Knowledge-base version must not be empty.")
    return get_terminology_service().load(module_name, version)


def resolve_module_path(
    module_name: str,
    *,
    version: str | None = None,
    for_write: bool = False,
) -> Path:
    """Resolve the source directory of the exact KB, never an unrelated default."""
    module_name = module_name.strip()
    kb = load_module_kb(module_name, version=version)
    config = kb.config
    if (
        config is None
        or config.name != module_name
        or (version is not None and config.version != version.strip())
    ):
        raise TerminologyError(
            409,
            "Resolved knowledge-base identity does not match the request.",
        )
    if config.source_file is None:
        raise TerminologyError(409, "Knowledge base has no attributable source file.")
    source = Path(config.source_file)
    if not source.is_absolute():
        raise TerminologyError(409, "Resolved module source must be an absolute path.")
    try:
        source = source.resolve(strict=True)
        if not source.is_file():
            raise ValueError("Module source must be a file")
    except (OSError, ValueError, RuntimeError) as exc:
        raise TerminologyError(409, "Resolved module source is unavailable.") from exc
    module_path = source.parent
    if module_path.name != module_name or source.name != "config.yaml":
        raise TerminologyError(
            409,
            "Module source is outside its named module directory.",
        )
    if for_write and module_path.is_relative_to(package_data_root().resolve()):
        raise TerminologyError(
            409,
            "Shipped data is read-only; hydrate or import an editable bundle first.",
        )
    return module_path
