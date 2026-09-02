from __future__ import annotations

from pathlib import Path


def package_data_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def default_data_roots() -> tuple[Path, ...]:
    """Return only the immutable data shipped in the installed package.

    Runtime deployments that need another knowledge-base version must resolve it
    explicitly through ``LX_DTYPES_KB_REGISTRY``. Checkout-relative and settings-
    based overlays made the effective clinical terminology depend on process
    working directory and are intentionally unsupported.
    """

    return (package_data_root(),)


def resolve_default_data_root() -> Path | None:
    roots = default_data_roots()
    for root in roots:
        if root.exists():
            return root
    return None
