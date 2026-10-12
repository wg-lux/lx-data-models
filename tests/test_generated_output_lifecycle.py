"""Legacy test exports have process-scoped storage, not persistent scratch files."""

import subprocess
import sys
from pathlib import Path


def test_generated_test_output_is_removed_at_process_exit() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from tests.paths import GENERATED_TEST_OUTPUT_ROOT as root; "
                "(root / 'export.yml').write_text('[]'); print(root)"
            ),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
    )
    assert not Path(completed.stdout.strip()).exists()
