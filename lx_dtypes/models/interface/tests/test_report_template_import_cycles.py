from __future__ import annotations

import subprocess
import sys


def _run_import_order(*modules: str) -> subprocess.CompletedProcess[str]:
    script = "\n".join(
        [
            "import os",
            "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lx_dtypes.django_settings_ci_test')",
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
