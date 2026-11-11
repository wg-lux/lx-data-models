import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from lx_dtypes import evaluation, validation
from lx_dtypes.evaluation import (
    parse_contract,
    parse_contract_json,
    validate_contract,
    validate_contract_json,
)
from lx_dtypes.evaluation.time import assess_time_offset
from lx_dtypes.models.contracts.time import ExaminationTimestamp, PtsTimestamp
from lx_dtypes.models.contracts.validation import ValidationReport
from lx_dtypes.models.contracts.video_text_metadata import VideoTextMetaPayload
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSection import (
    ReportTemplateSectionField,
)
from lx_dtypes.models.knowledge_base.time_reference import TimeReference
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.ledger.p_time_offset import PTimeOffset
from lx_dtypes.models.model import DtypesModel, DtypesRootModel
from lx_dtypes.packages import load_package


@pytest.mark.parametrize(
    "model, payload",
    [
        (
            PtsTimestamp,
            {
                "clock_id": "video",
                "ticks": 1000,
                "time_base_num": 1,
                "time_base_den": 1000,
            },
        ),
        (TimeReference, {"name": "time_event"}),
        (PExamination, {"patient": "synthetic", "examination": "synthetic"}),
        (ReportTemplateSectionField, {"key": "patient_name"}),
    ],
)
def test_all_layers_use_the_same_strict_and_advisory_boundary(
    model: type[BaseModel], payload: dict[str, object]
):
    value = parse_contract(model, payload)
    assert isinstance(value, DtypesModel)
    assert validate_contract(model, value).value == value
    invalid = {**payload, "unsupported": "private_value"}
    with pytest.raises(ValidationError):
        parse_contract(model, invalid)
    advisory = validate_contract(model, invalid)
    assert advisory.value is None
    assert [(issue.code, issue.path) for issue in advisory.report.issues] == [
        ("contract.extra_forbidden", ("unsupported",))
    ]
    assert "private_value" not in advisory.model_dump_json()


def test_json_uses_native_aware_datetime_rules_and_reports_invalid_json():
    payload = {"clock_id": "exam", "timestamp": "2026-01-01T12:00:00+02:00"}
    assert not validate_contract(ExaminationTimestamp, payload).report.ok
    value = parse_contract_json(ExaminationTimestamp, json.dumps(payload))
    assert value.timestamp == datetime(2026, 1, 1, 10, tzinfo=UTC)
    assert (
        validate_contract_json(ExaminationTimestamp, json.dumps(payload)).value == value
    )
    malformed = validate_contract_json(ExaminationTimestamp, '{"private_value":')
    assert not malformed.report.ok
    assert "private_value" not in malformed.model_dump_json()


def test_computed_fields_and_root_values_roundtrip_without_losing_their_schema():
    report = ValidationReport()
    assert parse_contract(ValidationReport, report) == report
    root = parse_contract(VideoTextMetaPayload, {"free_metadata_key": "value"})
    assert isinstance(root, DtypesRootModel)
    assert parse_contract_json(VideoTextMetaPayload, root.model_dump_json()) == root


def test_legacy_validation_exports_are_the_same_functions():
    assert validation.validate_contract is evaluation.validate_contract
    assert validation.assess_examination is evaluation.assess_examination


def test_backend_aggregation_reuses_the_canonical_registries():
    from lx_dtypes.models import main as models
    from lx_dtypes.models import pydantic_main
    from lx_dtypes.models.knowledge_base import main as kb_main
    from lx_dtypes.models.knowledge_base import pydantic_main as kb_pydantic
    from lx_dtypes.models.ledger import main as ledger_main
    from lx_dtypes.models.ledger import pydantic_main as ledger_pydantic
    from lx_dtypes.models.ledger.video_file import l_vid_file_django_lookup

    assert (
        kb_main.knowledge_base_models_lookup is kb_pydantic.knowledge_base_models_lookup
    )
    assert ledger_main.ledger_models_lookup is ledger_pydantic.ledger_models_lookup
    assert models.MODELS is pydantic_main.MODELS
    assert "VideoFileDjango" in l_vid_file_django_lookup


def test_all_registry_surfaces_are_available_without_django():
    statement = """
import importlib.abc
import sys
class BlockHost(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'django', 'ninja'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0, BlockHost())
from lx_dtypes.models import MODELS, MODEL_NAMES, DDICTS
from lx_dtypes.models.knowledge_base import knowledge_base_models_lookup
from lx_dtypes.models.ledger import ledger_models_lookup
from lx_dtypes.models.interface.Ledger import Ledger
from lx_dtypes.models.model import DtypesModel
from pydantic import BaseModel
for registry in (knowledge_base_models_lookup, ledger_models_lookup):
    for model in registry.values():
        if isinstance(model, type) and issubclass(model, BaseModel):
            assert issubclass(model, DtypesModel), model
assert 'VideoFileDjango' not in ledger_models_lookup
"""
    result = subprocess.run(
        [sys.executable, "-c", statement], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_time_assessment_reuses_kb_rules_and_does_not_hide_broken_configuration():
    kb = load_package(Path("docs/examples/dtypes_packages/time_references/config.yaml"))
    reference = kb.time_reference["video_generator_event"]
    observation = PTimeOffset(
        patient_examination="synthetic",
        time_reference=reference.name,
        knowledge_base_module=kb.config.name,
        knowledge_base_version=kb.config.version,
        evidence=reference.examples[0].evidence,
    )
    assert assess_time_offset(kb, observation).ok
    invalid = observation.model_copy(update={"knowledge_base_version": "wrong"})
    assert (
        assess_time_offset(kb, invalid).issues[0].code
        == "terminology.identity_mismatch"
    )
    unknown = observation.model_copy(update={"time_reference": "missing"})
    assert (
        assess_time_offset(kb, unknown).issues[0].code
        == "terminology.time_reference_unknown"
    )
    kb.time_reference[reference.name].kb_module_name = "unresolved"
    with pytest.raises(ValueError, match="resolved version"):
        assess_time_offset(kb, observation)
