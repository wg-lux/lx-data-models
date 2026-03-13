from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_MODULE_PATH = Path(__file__).resolve().parent / "lx_dtypes" / "utils" / "kb_yaml_lint.py"


def _load_runtime_module():
    spec = importlib.util.spec_from_file_location("lx_kb_yaml_lint_runtime", _MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load KB lint module: {_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    # Python 3.12 dataclasses resolve string annotations via sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_runtime = _load_runtime_module()

KbYamlLintIssue = _runtime.KbYamlLintIssue
discover_yaml_files = _runtime.discover_yaml_files
lint_kb_yaml_files = _runtime.lint_kb_yaml_files
summarize_issues = _runtime.summarize_issues

__all__ = [
    "KbYamlLintIssue",
    "discover_yaml_files",
    "lint_kb_yaml_files",
    "summarize_issues",
]
