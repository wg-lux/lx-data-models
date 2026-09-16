"""Runtime invariants must survive Python optimization."""

import subprocess
import sys

import pytest


@pytest.mark.parametrize("flags", [[], ["-O"]])
def test_runtime_checks_survive_optimization(flags: list[str]) -> None:
    script = """
import django
django.setup()
from lx_dtypes.models.meta.SensitiveMeta import SensitiveMeta
from lx_dtypes.models.ledger.p_video_segment.Pydantic import PVideoSegment
from lx_dtypes.models.interface.DbInterface import DbInterface
from lx_dtypes.models.meta.SensitiveMeta import SensitiveMetaState
from types import SimpleNamespace

choices = SimpleNamespace(uuid="choices", patient_finding_classification_choices=[])
finding = SimpleNamespace(finding="finding", latest_classifications_obj=choices)
exam = SimpleNamespace(get_finding_by_uuid=lambda value: finding)
kb_finding = SimpleNamespace(name="finding", classifications=[])
kb = SimpleNamespace(
    get_finding=lambda name: kb_finding,
    get_classification=lambda name: SimpleNamespace(classification_choices=[]),
    get_classification_choice=lambda name: object(),
)
interface = SimpleNamespace(
    knowledge_base=kb,
    ledger=SimpleNamespace(p_examination_exists=lambda value: True, patient_examinations={"exam": exam}),
)
for linked in [False, True]:
    kb_finding.classifications = ["classification"] if linked else []
    try:
        DbInterface.create_patient_finding_classification_choice(
            interface, "exam", "finding", "classification", "choice"
        )
    except ValueError as exc:
        expected = "does not belong" if linked else "not linked"
        if expected not in str(exc):
            raise
    else:
        raise RuntimeError("Invalid relationship was accepted")
if choices.patient_finding_classification_choices:
    raise RuntimeError("Rejected choice mutated the ledger")

checks = [
    (lambda: SensitiveMeta.model_construct(sensitive_meta_state=None).state, ValueError),
    (lambda: PVideoSegment.model_construct(patient_video_segment_state=None).state, ValueError),
    (lambda: SensitiveMeta.model_validate({
        "sensitive_meta_state": SensitiveMetaState(sensitive_meta="wrong")
    }), ValueError),
    (lambda: DbInterface.model_construct().create_classification_choice_descriptor(
        "missing", "missing", "missing", {}
    ), NotImplementedError),
]
for check, expected in checks:
    try:
        check()
    except expected:
        pass
    else:
        raise RuntimeError(f"Expected {expected.__name__}")
"""
    result = subprocess.run(
        [sys.executable, *flags, "-c", script],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, result.stderr
