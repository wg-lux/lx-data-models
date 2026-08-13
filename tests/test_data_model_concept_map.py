from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import cast, get_args

from pydantic import BaseModel, ValidationError
import pytest
import yaml

import lx_dtypes.models.contracts as contract_models
import lx_dtypes.models.knowledge_base.report_template as report_template_models

from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import AppBaseModel
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelNamesUUIDTags import (
    AppBaseModelNamesUUIDTags,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.base.app_base_model.pydantic.MetaBaseModel import MetaBaseModel
from lx_dtypes.models.base.app_base_model.pydantic.StateBaseModel import StateBaseModel
from lx_dtypes.models.contracts import CoreConceptCollection
from lx_dtypes.models.contracts.adapters import kb_to_core_concepts_payload
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.knowledge_base.main import (
    KB_MODELS,
    KB_MODEL_NAMES_ORDERED,
)
from lx_dtypes.models.ledger.main import L_MODELS, L_MODEL_NAMES_ORDERED
from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReference import (
    ValidatorRequirementKind,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = REPOSITORY_ROOT / "docs" / "data-model-concept-map.yml"
GUIDE_PATH = REPOSITORY_ROOT / "docs" / "guides" / "data-model-concept-map.md"


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return cast(dict[str, object], value)


def _sequence(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast(list[object], value)


def _strings(value: object) -> list[str]:
    values = _sequence(value)
    assert all(isinstance(item, str) for item in values)
    return cast(list[str], values)


def _load_map() -> dict[str, object]:
    return _mapping(yaml.safe_load(MAP_PATH.read_text(encoding="utf-8")))


def _levels() -> dict[int, dict[str, object]]:
    levels = [_mapping(level) for level in _sequence(_load_map()["levels"])]
    result = {cast(int, level["id"]): level for level in levels}
    assert len(result) == len(levels)
    return result


def _runtime_models(union: object) -> dict[str, type[BaseModel]]:
    models = get_args(union)
    assert all(
        isinstance(model, type) and issubclass(model, BaseModel) for model in models
    )
    return {
        model.__name__: model for model in cast(tuple[type[BaseModel], ...], models)
    }


def _snake_case(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def test_concept_map_has_supported_structure_and_existing_sources() -> None:
    data = _load_map()

    assert data["schema_version"] == "1.0"
    assert set(_levels()) == set(range(6))
    assert data["owner"] == "lx-data-models maintainers"

    for location in _mapping(data["source_locations"]).values():
        assert isinstance(location, str)
        assert (REPOSITORY_ROOT / location).exists()


def test_concept_map_inheritance_and_shared_fields_match_models() -> None:
    level = _levels()[1]
    model_by_name: dict[str, type[BaseModel]] = {
        model.__name__: model
        for model in (
            AppBaseModel,
            AppBaseModelUUIDTags,
            AppBaseModelNamesUUIDTags,
            KnowledgebaseBaseModel,
            LedgerBaseModel,
            MetaBaseModel,
            StateBaseModel,
        )
    }

    for relation in _sequence(level["inheritance"]):
        parent_name, child_name = _strings(relation)
        assert issubclass(model_by_name[child_name], model_by_name[parent_name])

    for model_name, fields_value in _mapping(level["shared_fields"]).items():
        assert set(_strings(fields_value)) <= set(
            model_by_name[model_name].model_fields
        )


def test_concept_map_registries_and_fields_match_runtime_models() -> None:
    levels = _levels()
    kb_models = _runtime_models(KB_MODELS)
    ledger_models = _runtime_models(L_MODELS)

    terminology = _mapping(levels[2]["concepts"])
    report_concepts = _mapping(levels[4]["concepts"])
    report_model_names = {
        "ReportTemplate",
        "ReportTemplateSection",
        "ReportFinding",
        *_strings(report_concepts["validators"]),
    }
    documented_kb_names = set(terminology) | report_model_names
    assert documented_kb_names == set(kb_models) == set(KB_MODEL_NAMES_ORDERED)

    field_groups = {
        name: _strings(fields)
        for name, fields in _mapping(_load_map()["field_groups"]).items()
    }
    ledger_sections = (
        "context_concepts",
        "finding_branch",
        "indication_branch",
        "medical_branch",
        "media_branch",
    )
    documented_ledger: dict[str, list[str]] = {}
    for section in ledger_sections:
        documented_ledger.update(
            {
                name: _strings(fields)
                for name, fields in _mapping(levels[3][section]).items()
            }
        )
    assert set(documented_ledger) == set(ledger_models) == set(L_MODEL_NAMES_ORDERED)

    for model_name, specification in terminology.items():
        fields = _mapping(specification).get("fields", [])
        assert set(_strings(fields)) <= set(kb_models[model_name].model_fields)

    for model_name in ("ReportTemplate", "ReportTemplateSection", "ReportFinding"):
        fields = _strings(_mapping(report_concepts[model_name])["fields"])
        assert set(fields) <= set(kb_models[model_name].model_fields)

    for model_name, fields in documented_ledger.items():
        model_fields = set(ledger_models[model_name].model_fields)
        for field in fields:
            if field in field_groups:
                assert set(field_groups[field]) <= model_fields
            else:
                assert field in model_fields


def test_concept_map_lists_every_contract_module_exactly_once() -> None:
    families = _mapping(_levels()[5]["families"])
    documented = [
        module for modules in families.values() for module in _strings(modules)
    ]
    module_files = {
        path.stem
        for path in (REPOSITORY_ROOT / "lx_dtypes" / "models" / "contracts").glob(
            "*.py"
        )
        if path.stem != "__init__"
    }

    assert not [module for module, count in Counter(documented).items() if count > 1]
    assert set(documented) == module_files


def test_every_documented_terminology_relation_is_enforced_by_snapshot() -> None:
    relations = _sequence(_levels()[2]["relations"])

    for relation_value in relations:
        source_name, reference_field, target_name = _strings(relation_value)
        source_collection = _snake_case(source_name)
        target_collection = _snake_case(target_name)
        reference_value: str | list[str] = (
            "missing_target" if reference_field == "unit" else ["missing_target"]
        )
        payload: dict[str, object] = {
            "module_name": "contract_test",
            source_collection: [{"name": "source", reference_field: reference_value}],
        }

        with pytest.raises(ValidationError):
            CoreConceptCollection.model_validate(payload)

        payload[target_collection] = [{"name": "missing_target"}]
        CoreConceptCollection.model_validate(payload)


def test_every_packaged_knowledge_base_exports_a_complete_snapshot() -> None:
    loader = DataLoader(input_dirs=[REPOSITORY_ROOT / "lx_dtypes" / "data"])
    loader.load_module_configs()

    assert loader.module_configs
    assert all(
        len(candidates) == 1 for candidates in loader.module_config_candidates.values()
    )
    for module_name in sorted(loader.module_configs):
        snapshot = kb_to_core_concepts_payload(loader.load_knowledge_base(module_name))
        assert snapshot.knowledge_base_module == module_name
        assert snapshot.knowledge_base_version


def test_report_contract_inventory_names_public_runtime_types() -> None:
    concepts = _mapping(_levels()[4]["concepts"])
    requirement = _mapping(concepts["validator_requirement"])

    assert set(_strings(requirement["kinds"])) == set(
        cast(tuple[str, ...], get_args(ValidatorRequirementKind))
    )
    assert hasattr(report_template_models, cast(str, requirement["model"]))
    for model_name in _strings(concepts["derived_structures"]):
        assert hasattr(report_template_models, model_name)
    for model_name in _strings(concepts["runtime_contracts"]):
        assert hasattr(contract_models, model_name)


def test_public_guide_counts_and_scope_follow_machine_map() -> None:
    guide = " ".join(GUIDE_PATH.read_text(encoding="utf-8").split())
    terminology = _mapping(_levels()[2]["concepts"])
    type_count = sum(
        _mapping(specification).get("kind") == "type"
        for specification in terminology.values()
    )

    assert f"aggregates {len(KB_MODEL_NAMES_ORDERED)} registered model types" in guide
    assert f"itself has {len(terminology)} concepts; {type_count} are" in guide
    assert f"registry contains {len(L_MODEL_NAMES_ORDERED)} named model types" in guide
    assert "RawPatientVideoFile" not in guide
