"""Exercise real Django stubs through the repository's configured type checker."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tests.paths import REPOSITORY_ROOT


@pytest.mark.parametrize(
    ("source", "expected_errors"),
    [
        (
            """
from datetime import datetime
from typing import assert_type
import django
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db import IntegrityError, models, transaction
from django.db.models import QuerySet
from django.utils import timezone

assert_type(django.setup(), None)
assert_type(timezone.now(), datetime)
assert_type(IntegrityError("invalid"), IntegrityError)
assert_type(get_user_model(), type[AbstractBaseUser])
assert_type(admin.site, admin.AdminSite)
name: models.CharField[str, str] = models.CharField(max_length=80)

def read_rows(rows: QuerySet[models.Model]) -> int:
    with transaction.atomic():
        return rows.count()
""",
            0,
        ),
        (
            """
from django.db import models
name: models.CharField[str, str] = models.CharField(max_length="invalid")
""",
            1,
        ),
        (
            """
from django.utils import timezone
instant: int = timezone.now()
""",
            1,
        ),
    ],
    ids=[
        "django-public-api",
        "reject-invalid-field-argument",
        "reject-invalid-return-type",
    ],
)
def test_django_typing_contract_aaa(
    tmp_path: Path, source: str, expected_errors: int
) -> None:
    # Arrange: isolate the probe from pytest runtime and use the production type configuration.
    probe = tmp_path / "django_typing_probe.py"
    probe.write_text(source, encoding="utf-8")

    # Act: do not override the interpreter; configuration must select this repository's venv.
    result = subprocess.run(
        [
            "pyright",
            "--project",
            str(REPOSITORY_ROOT / "pyproject.toml"),
            "--outputjson",
            str(probe),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    # Assert: valid APIs resolve, while real type mismatches remain visible.
    report = json.loads(result.stdout)
    assert report["summary"]["errorCount"] == expected_errors, (
        result.stdout + result.stderr
    )
    assert result.returncode == (1 if expected_errors else 0), (
        result.stdout + result.stderr
    )
    diagnostics = report["generalDiagnostics"]
    assert all(
        diagnostic.get("rule") in {"reportArgumentType", "reportAssignmentType"}
        for diagnostic in diagnostics
    ), diagnostics
