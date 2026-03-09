"""Pytest settings for lx_dtypes API contract tests.

This module forces an isolated test configuration so local/prod environment
variables (for example `DJANGO_SETTINGS_MODULE=...settings_prod`) do not leak
into pytest runs.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, cast

try:
    # Preferred in the monorepo: tested baseline with in-memory SQLite
    from lx_annotate.settings.settings_test import *  # type: ignore # noqa: F401,F403
except Exception:  # pragma: no cover - fallback for standalone lx-data-models usage
    from lx_dtypes.django_settings import *  # type: ignore # noqa: F401,F403

    INSTALLED_APPS = list(INSTALLED_APPS)  # type: ignore[name-defined]

    required_apps = [
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "endoreg_db",
        "rest_framework",
    ]

    for app in required_apps:
        if app not in INSTALLED_APPS:
            INSTALLED_APPS.append(app)

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
    MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="lx_dtypes_test_media_"))
    STATIC_ROOT = str(Path(tempfile.mkdtemp(prefix="lx_dtypes_test_static_")))
    SECRET_KEY = "lx-dtypes-test-secret"
    DEBUG = True

INSTALLED_APPS = list(INSTALLED_APPS)  # type: ignore[name-defined]
if "lx_dtypes.django.apps.LxDtypesDjangoConfig" not in INSTALLED_APPS:
    INSTALLED_APPS.append("lx_dtypes.django.apps.LxDtypesDjangoConfig")

if "endoreg_db" not in INSTALLED_APPS:
    INSTALLED_APPS.append("endoreg_db")

ROOT_URLCONF = "lx_dtypes.django.urls"

# Keep dtypes-backed findings API tests deterministic in CI by using a
# guaranteed module from lx_dtypes/data, unless explicitly overridden.
os.environ.setdefault("LX_DTYPES_FINDINGS_MODULE", "report_template_examples")
