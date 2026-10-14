from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_knowledge_base_import_does_not_require_django_settings() -> None:
    project_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment.pop("DJANGO_SETTINGS_MODULE", None)
    environment["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from lx_dtypes.models.interface.KnowledgeBase "
                "import KnowledgeBase\n"
                "from django.conf import settings\n"
                "assert not settings.configured\n"
                "assert not any("
                "name.rsplit('.', 1)[-1].endswith('Django') "
                "for name in sys.modules"
                ")\n"
                "assert KnowledgeBase.__module__ == "
                "'lx_dtypes.models.interface.KnowledgeBase'\n"
            ),
        ],
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
