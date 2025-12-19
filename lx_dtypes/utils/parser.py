from pathlib import Path
from typing import Any, Dict, List, Union

import yaml

from lx_dtypes.models.core import (
    CitationShallow,
    ExaminationShallow,
    InformationSourceShallow,
)
from lx_dtypes.models.core.center_shallow import CenterShallow
from lx_dtypes.models.core.classification_choice_descriptor_shallow import (
    ClassificationChoiceDescriptorShallow,
)
from lx_dtypes.models.core.classification_choice_shallow import (
    ClassificationChoiceShallow,
)
from lx_dtypes.models.core.classification_shallow import (
    ClassificationShallow,
    ClassificationTypeShallow,
)
from lx_dtypes.models.core.examination_shallow import ExaminationTypeShallow
from lx_dtypes.models.core.finding_shallow import FindingShallow, FindingTypeShallow
from lx_dtypes.models.core.indication_shallow import (
    IndicationShallow,
    IndicationTypeShallow,
)
from lx_dtypes.models.core.intervention_shallow import (
    InterventionShallow,
    InterventionTypeShallow,
)
from lx_dtypes.models.core.unit_shallow import UnitShallow, UnitTypeShallow
from lx_dtypes.utils.factories.field_defaults import str_unknown_factory

model_types = Union[
    type[CenterShallow],
    type[InformationSourceShallow],
    type[CitationShallow],
    type[ExaminationShallow],
    type[ExaminationTypeShallow],
    type[FindingShallow],
    type[FindingTypeShallow],
    type[ClassificationShallow],
    type[ClassificationChoiceShallow],
    type[ClassificationChoiceDescriptorShallow],
    type[ClassificationTypeShallow],
    type[IndicationShallow],
    type[IndicationTypeShallow],
    type[InterventionShallow],
    type[InterventionTypeShallow],
    type[UnitShallow],
    type[UnitTypeShallow],
]

ShallowModel = Union[
    CenterShallow,
    InformationSourceShallow,
    CitationShallow,
    ExaminationShallow,
    ExaminationTypeShallow,
    FindingShallow,
    FindingTypeShallow,
    ClassificationShallow,
    ClassificationChoiceShallow,
    ClassificationChoiceDescriptorShallow,
    ClassificationTypeShallow,
    IndicationShallow,
    IndicationTypeShallow,
    InterventionShallow,
    InterventionTypeShallow,
    UnitShallow,
    UnitTypeShallow,
]

model_lookup: Dict[str, model_types] = {
    "center": CenterShallow,
    "information_source": InformationSourceShallow,
    "citation": CitationShallow,
    "examination": ExaminationShallow,
    "examination_type": ExaminationTypeShallow,
    "finding": FindingShallow,
    "finding_type": FindingTypeShallow,
    "classification": ClassificationShallow,
    "classification_choice": ClassificationChoiceShallow,
    "classification_choice_descriptor": ClassificationChoiceDescriptorShallow,
    "classification_type": ClassificationTypeShallow,
    "indication": IndicationShallow,
    "indication_type": IndicationTypeShallow,
    "intervention": InterventionShallow,
    "intervention_type": InterventionTypeShallow,
    "unit": UnitShallow,
    "unit_type": UnitTypeShallow,
}

allowed_types = [v for _, v in model_lookup.items()]

reverse_model_lookup: Dict[model_types, str] = {v: k for k, v in model_lookup.items()}


def parse_shallow_object(
    file_path: Path, kb_module_name: str = str_unknown_factory()
) -> List[ShallowModel]:
    if not file_path.exists() or not file_path.is_file():
        raise ValueError(
            f"The provided path {file_path} does not exist or is not a file."
        )

    assert file_path.suffix == ".yaml" or file_path.suffix == ".yml", (
        "File must be a YAML file."
    )

    # each yaml file is a list of objects
    with file_path.open("r", encoding="utf-8") as f:
        data: List[Dict[str, Any]] = yaml.safe_load(f) or []  # simplified typ

    assert isinstance(data, list), "YAML file must contain a list of objects."
    results: List[ShallowModel] = list()
    for item in data:
        assert isinstance(item, dict), "Each item in the list must be a dictionary."

        target_model_name = item.get("model")
        assert target_model_name is not None, "Each item must have a 'model' field."

        TargetModel = model_lookup.get(target_model_name, None)
        assert TargetModel is not None, f"Unknown model type: {target_model_name}"

        item.pop("model")  # remove the model field before validation
        item["kb_module_name"] = kb_module_name  # set the kb_module for reference
        item["source_file"] = file_path  # set source_file for reference
        result = TargetModel.model_validate(item)
        result_type = type(result)
        assert result_type in allowed_types, (
            f"Parsed object type {result_type} is not allowed."
        )

        results.append(result)
    return results
