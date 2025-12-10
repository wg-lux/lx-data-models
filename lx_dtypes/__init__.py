"""Public exports for the lx_dtypes package."""

from importlib import metadata as _metadata

try:
    __version__ = _metadata.version("lx-dtypes")
except _metadata.PackageNotFoundError:  # pragma: no cover - only during local dev
    __version__ = "0.0.0"

__all__ = ["__version__"]
