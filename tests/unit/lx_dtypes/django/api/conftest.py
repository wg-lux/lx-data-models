"""Isolated storage for API tests that exercise the central terminology resolver."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from pytest_django.fixtures import SettingsWrapper

from lx_dtypes.terminology import terminology_loader as central
from lx_dtypes.terminology.lookup_tracker import consume_runtime_lookup_trackers


@pytest.fixture
def terminology_root(tmp_path: Path, settings: SettingsWrapper) -> Iterator[Path]:
    """Configure a fresh root; each test supplies the registry/artifacts it needs.

    This does not rebind services already captured by route registration. Tests
    using terminology write routes must register a fresh API with this service.
    """
    from lx_dtypes.django.api import main as api_main

    root = tmp_path / "terminology"
    root.mkdir()
    settings.TERMINOLOGY_ROOT = root
    central.get_terminology_service.cache_clear()
    api_main._clear_kb_caches()
    consume_runtime_lookup_trackers()
    try:
        yield root
    finally:
        consume_runtime_lookup_trackers()
        api_main._clear_kb_caches()
        central.get_terminology_service.cache_clear()
