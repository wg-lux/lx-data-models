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
                "from pathlib import Path\n"
                "from lx_dtypes.models.interface.DataLoader import DataLoader\n"
                "from lx_dtypes.validation import assess_examination\n"
                "loader = DataLoader(input_dirs=[Path('lx_dtypes/data')])\n"
                "loader.load_module_configs()\n"
                "kb = loader.load_knowledge_base('report_template_examples')\n"
                "report = assess_examination(kb, {\n"
                "    'patient': 'synthetic-patient',\n"
                "    'examination': 'star_upper_gi_endoscopy',\n"
                "    **kb.config.knowledge_base_identity.model_dump(),\n"
                "})\n"
                "assert report.ok, report\n"
                "invalid = assess_examination(kb, {'patient': ''})\n"
                "assert not invalid.ok and invalid.issues\n"
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


def test_ledger_django_registry_preserves_explicit_exports() -> None:
    from lx_dtypes.models.ledger import ledger_models_django_lookup
    from lx_dtypes.models.ledger.p_examination import (
        PExaminationDjango,
        l_p_examination_django_lookup,
        l_p_examination_django_models,
    )

    assert ledger_models_django_lookup["PExamination"] is PExaminationDjango
    assert l_p_examination_django_lookup["PExamination"] is PExaminationDjango
    assert l_p_examination_django_models is PExaminationDjango
