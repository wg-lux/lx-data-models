from __future__ import annotations

from pathlib import Path


def _configured_lookup_data_root() -> Path | None:
    configured_path = ""
    try:
        from django.conf import settings

        configured_path = str(getattr(settings, "LOOKUP_DTYPES_DATA_ROOT", "")).strip()
    except Exception:
        configured_path = ""

    if not configured_path:
        return None

    configured_root = Path(configured_path).expanduser().resolve()
    if configured_root.exists():
        return configured_root
    return None


def package_data_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def repo_data_root() -> Path:
    return Path("./lx_dtypes/data/").resolve()


def default_data_roots() -> tuple[Path, ...]:
    configured_root = _configured_lookup_data_root()
    if configured_root is not None:
        return (configured_root,)

    package_root = package_data_root()
    legacy_root = repo_data_root()
    existing_roots = tuple(
        data_root
        for data_root in (package_root, legacy_root)
        if data_root.exists()
    )
    return existing_roots or (package_root,)


def resolve_default_data_root() -> Path | None:
    roots = default_data_roots()
    for root in roots:
        if root.exists():
            return root
    return None
