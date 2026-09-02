"""Stable repository paths for tests that inspect packaged source data."""

from pathlib import Path
from tempfile import mkdtemp

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "lx_dtypes"
GENERATED_TEST_OUTPUT_ROOT = Path(mkdtemp(prefix="lx_dtypes_test_outputs_"))
