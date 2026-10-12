"""Compatibility import for the canonical Django terminology HTTP adapter."""

from lx_dtypes.django.api.terminology_routes import (
    register_terminology_routes,
)

__all__ = ["register_terminology_routes"]
