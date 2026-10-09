from __future__ import annotations

import subprocess
import sys

import pytest


def _run_import_order(*modules: str) -> subprocess.CompletedProcess[str]:
    script = "\n".join(
        [
            "import os",
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.django_settings')",
            "import django",
            "django.setup()",
            "import importlib",
            *[f"importlib.import_module('{module}')" for module in modules],
        ]
    )
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )


def test_import_order_knowledge_base_then_compiler_then_validator() -> None:
    result = _run_import_order(
        "lx_dtypes.models.interface.KnowledgeBase",
        "lx_dtypes.models.interface.ReportTemplateCompiler",
        "lx_dtypes.models.interface.ReportTemplateValidator",
    )
    assert result.returncode == 0, result.stderr


def test_import_order_compiler_then_knowledge_base_then_validator() -> None:
    result = _run_import_order(
        "lx_dtypes.models.interface.ReportTemplateCompiler",
        "lx_dtypes.models.interface.KnowledgeBase",
        "lx_dtypes.models.interface.ReportTemplateValidator",
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "modules",
    [
        ("validators.ValidatorRuntime", "fhir.findings", "report_template"),
        ("fhir.findings", "report_template", "validators.ValidatorRuntime"),
        ("report_template", "validators.ValidatorRuntime", "fhir.findings"),
        ("validators", "fhir", "report_template.ValidatorRuntime"),
    ],
)
def test_functionality_packages_import_in_any_order(modules: tuple[str, ...]) -> None:
    result = _run_import_order(
        *(f"lx_dtypes.models.knowledge_base.{name}" for name in modules),
        "lx_dtypes.models.interface.KnowledgeBase",
    )
    assert result.returncode == 0, result.stderr
