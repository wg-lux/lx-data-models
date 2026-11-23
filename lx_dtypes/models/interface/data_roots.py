"""Locations of the knowledge-base data shipped inside the installed package."""

from __future__ import annotations

from pathlib import Path


def package_data_root() -> Path:
    """Return the ``lx_dtypes/data`` directory of the installed package."""
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
    """Return the first packaged data root that exists, or ``None``.

    The returned path contains only the immutable data bundled with this
    installation. It is not influenced by the working directory or settings.
    """
    roots = default_data_roots()
    for root in roots:
        if root.exists():
            return root
    return None


def module_search_root(config_path: Path) -> Path:
    """Include sibling definition categories for current packaged manifests.

    Historical bundles and independently authored module trees retain their
    enclosing directory as the discovery scope.
    """
    root = config_path.parent.parent
    for ancestor in config_path.parents:
        if ancestor.name == "versions":
            break
        if (
            ancestor.name in {"terminology", "report_templates"}
            and ancestor.parent.name == "data"
        ):
            return ancestor.parent
    return root
