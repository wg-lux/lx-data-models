"""Run framework-double terminology checks in their required isolated process."""

import os
import subprocess
import sys

from tests.paths import REPOSITORY_ROOT


def test_isolated_terminology_verification():
    directory = REPOSITORY_ROOT / "tests/isolated/terminology"
    environment = os.environ.copy()
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-c",
            os.devnull,
            f"--confcutdir={directory}",
            "-p",
            "tests.isolated.terminology.harness",
            *(str(path) for path in sorted(directory.glob("checks_*.py"))),
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    assert result.returncode == 0, result.stdout + result.stderr
