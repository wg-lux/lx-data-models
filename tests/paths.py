"""Stable repository paths for tests that inspect packaged source data."""

from pathlib import Path
from tempfile import TemporaryDirectory

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "lx_dtypes"
_generated_test_outputs = TemporaryDirectory(prefix="lx_dtypes_test_outputs_")
GENERATED_TEST_OUTPUT_ROOT = Path(_generated_test_outputs.name)
