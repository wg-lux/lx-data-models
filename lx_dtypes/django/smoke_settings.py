"""Isolated Django settings for the packaged knowledge-base smoke command."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, cast

from lx_dtypes.django_settings import *  # type: ignore

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


class DisableMigrations:
    def __contains__(self, item: object) -> bool:
        return True

    def __getitem__(self, item: object) -> None:
        return None


MIGRATION_MODULES = cast(Any, DisableMigrations())
MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="lx_dtypes_smoke_media_"))
STATIC_ROOT = str(Path(tempfile.mkdtemp(prefix="lx_dtypes_smoke_static_")))
SECRET_KEY = "lx-dtypes-smoke-secret"
DEBUG = False

_package_data_root = Path(__file__).resolve().parents[1] / "data"
_registry_dir = Path(tempfile.mkdtemp(prefix="lx_dtypes_smoke_registry_"))
_registry_path = _registry_dir / "registry.json"
_registry_path.write_text(
    json.dumps(
        {
            "active": {
                "module_name": "report_template_examples",
                "version": "0.1.1",
            },
            "modules": {
                "report_template_examples": {
                    "0.1.1": {"input_dirs": [str(_package_data_root)]}
                }
            },
        }
    ),
    encoding="utf-8",
)
os.environ.setdefault("LX_DTYPES_KB_REGISTRY", str(_registry_path))
