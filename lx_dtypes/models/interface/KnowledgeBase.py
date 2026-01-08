from pathlib import Path
from typing import Dict, Self, TypedDict, Union, cast

import yaml
from pydantic import Field

from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base import (
    KB_MODEL_NAMES_ORDERED,
    KB_MODELS,
    knowledge_base_models_lookup,
)
from lx_dtypes.models.knowledge_base.classification.Classification import (
    Classification,
)
from lx_dtypes.models.knowledge_base.classification.ClassificationDataDict import (
    ClassificationDataDict,
)
from lx_dtypes.models.knowledge_base.classification.ClassificationType import (
    ClassificationType,
)
from lx_dtypes.models.knowledge_base.classification.ClassificationTypeDataDict import (
    ClassificationTypeDataDict,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDataDict import (
    ClassificationChoiceDataDict,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDataDict import (
    ClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.knowledge_base.examination.Examination import Examination
from lx_dtypes.models.knowledge_base.examination.ExaminationDataDict import (
    ExaminationDataDict,
)
from lx_dtypes.models.knowledge_base.examination.ExaminationType import ExaminationType
from lx_dtypes.models.knowledge_base.examination.ExaminationTypeDataDict import (
    ExaminationTypeDataDict,
)
from lx_dtypes.models.knowledge_base.finding.Finding import Finding
from lx_dtypes.models.knowledge_base.finding.FindingDataDict import FindingDataDict
from lx_dtypes.models.knowledge_base.finding.FindingType import FindingType
from lx_dtypes.models.knowledge_base.finding.FindingTypeDataDict import (
    FindingTypeDataDict,
)
from lx_dtypes.models.knowledge_base.indication.Indication import Indication
from lx_dtypes.models.knowledge_base.indication.IndicationDataDict import (
    IndicationDataDict,
)
from lx_dtypes.models.knowledge_base.indication.IndicationType import IndicationType
from lx_dtypes.models.knowledge_base.indication.IndicationTypeDataDict import (
    IndicationTypeDataDict,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSource import (
    InformationSource,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceDataDict import (
    InformationSourceDataDict,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceType import (
    InformationSourceType,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceTypeDataDict import (
    InformationSourceTypeDataDict,
)
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.intervention.InterventionDataDict import (
    InterventionDataDict,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionType import (
    InterventionType,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionTypeDataDict import (
    InterventionTypeDataDict,
)
from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitDataDict import UnitDataDict
from lx_dtypes.models.knowledge_base.unit.UnitType import UnitType
from lx_dtypes.models.knowledge_base.unit.UnitTypeDataDict import UnitTypeDataDict
from lx_dtypes.utils.parser import camel_to_snake, parse_shallow_object, snake_to_camel


class KnowledgeBaseDDict(AppBaseModelUUIDTagsDataDict):
    config: KnowledgeBaseConfig
    classification: Dict[str, ClassificationDataDict]
    classification_type: Dict[str, ClassificationTypeDataDict]
    classification_choice: Dict[str, ClassificationChoiceDataDict]
    classification_choice_descriptor: Dict[str, ClassificationChoiceDescriptorDataDict]
    examination: Dict[str, ExaminationDataDict]
    examination_type: Dict[str, ExaminationTypeDataDict]
    finding: Dict[str, FindingDataDict]
    finding_type: Dict[str, FindingTypeDataDict]
    indication: Dict[str, IndicationDataDict]
    indication_type: Dict[str, IndicationTypeDataDict]
    intervention: Dict[str, InterventionDataDict]
    intervention_type: Dict[str, InterventionTypeDataDict]
    unit_type: Dict[str, UnitTypeDataDict]
    unit: Dict[str, UnitDataDict]
    information_source: Dict[str, InformationSourceDataDict]
    information_source_type: Dict[str, InformationSourceTypeDataDict]


YAML_IMPORT_SKIP_FIELDS = ["config", "uuid", "source_file", "created_at", "updated_at"]


class KnowledgeBase(AppBaseModelUUIDTags):
    config: KnowledgeBaseConfig
    classification: Dict[str, Classification] = Field(default_factory=dict)
    classification_type: Dict[str, ClassificationType] = Field(default_factory=dict)
    classification_choice: Dict[str, ClassificationChoice] = Field(default_factory=dict)
    classification_choice_descriptor: Dict[str, ClassificationChoiceDescriptor] = Field(
        default_factory=dict
    )
    examination: Dict[str, Examination] = Field(default_factory=dict)
    examination_type: Dict[str, ExaminationType] = Field(default_factory=dict)
    finding: Dict[str, Finding] = Field(default_factory=dict)
    finding_type: Dict[str, FindingType] = Field(default_factory=dict)
    indication: Dict[str, Indication] = Field(default_factory=dict)
    indication_type: Dict[str, IndicationType] = Field(default_factory=dict)
    intervention: Dict[str, Intervention] = Field(default_factory=dict)
    intervention_type: Dict[str, InterventionType] = Field(default_factory=dict)
    unit_type: Dict[str, UnitType] = Field(default_factory=dict)
    unit: Dict[str, Unit] = Field(default_factory=dict)
    information_source: Dict[str, InformationSource] = Field(default_factory=dict)
    information_source_type: Dict[str, InformationSourceType] = Field(
        default_factory=dict
    )

    def get_classification(self, name: str) -> Classification:
        return self.classification[name]

    def get_classification_type(self, name: str) -> ClassificationType:
        return self.classification_type[name]

    def get_classification_choice(self, name: str) -> ClassificationChoice:
        return self.classification_choice[name]

    def get_classification_choice_descriptor(
        self, name: str
    ) -> ClassificationChoiceDescriptor:
        return self.classification_choice_descriptor[name]

    def get_examination(self, name: str) -> Examination:
        return self.examination[name]

    def get_examination_type(self, name: str) -> ExaminationType:
        return self.examination_type[name]

    def get_finding(self, name: str) -> Finding:
        return self.finding[name]

    def get_finding_type(self, name: str) -> FindingType:
        return self.finding_type[name]

    def get_indication(self, name: str) -> Indication:
        return self.indication[name]

    def get_indication_type(self, name: str) -> IndicationType:
        return self.indication_type[name]

    def get_intervention(self, name: str) -> Intervention:
        return self.intervention[name]

    def get_intervention_type(self, name: str) -> InterventionType:
        return self.intervention_type[name]

    def get_unit_type(self, name: str) -> UnitType:
        return self.unit_type[name]

    def get_unit(self, name: str) -> Unit:
        return self.unit[name]

    @property
    def ddict_class(self) -> type[KnowledgeBaseDDict]:
        return KnowledgeBaseDDict

    @property
    def ddict(self) -> KnowledgeBaseDDict:
        return self.ddict_class(**self.model_dump())

    @classmethod
    def create_from_config(cls, config: "KnowledgeBaseConfig") -> "KnowledgeBase":
        name = config.name
        # source_file = config.source_file
        # assert source_file is not None, "Config must have source_file set." # Can be removed?
        kb_source_dict: Dict[str, Union["KnowledgeBaseConfig", Path]] = {
            "config": config,
            # "source_file": source_file,  # Can be removed?
        }
        kb = cls.model_validate(kb_source_dict)
        data = config.data
        submodule_files = data.get_files_with_suffix(".yaml")
        for sm_file in submodule_files:
            parsed_object_generator = parse_shallow_object(sm_file, kb_module_name=name)
            for parsed_object in parsed_object_generator:
                model_name = camel_to_snake(type(parsed_object).__name__)
                object_name = parsed_object.name
                if not hasattr(kb, model_name):
                    raise ValueError(f"KnowledgeBase has no attribute '{model_name}'")
                model_dict: Dict[str, KB_MODELS] = getattr(kb, model_name)
                if object_name in model_dict:
                    pass  # or raise warning?
                model_dict[object_name] = parsed_object

                # set the updated dict back to the kb
                setattr(kb, model_name, model_dict)
        return kb

    @classmethod
    def create_from_yaml(cls, yaml_path: Path) -> Self:
        """Load a knowledge base from a YAML dump.

        Args:
            yaml_path (Path): The path to the YAML file.
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            data_dict = yaml.safe_load(f)

        kb = cls.model_validate(data_dict)
        return kb

    def import_knowledge_base(self, other: "KnowledgeBase") -> None:
        """Merge another KnowledgeBase into this one.

        Args:
            other (KnowledgeBase): The other KnowledgeBase to merge.
        """
        for field_name in KnowledgeBase.model_fields:
            field_model_name = snake_to_camel(field_name)
            if field_name in YAML_IMPORT_SKIP_FIELDS:
                continue  # skip config

            if field_name == "tags":
                current_tags = set(getattr(self, "tags", []))
                other_tags = set(getattr(other, "tags", []))
                merged_tags = list(current_tags.union(other_tags))
                setattr(self, field_name, merged_tags)
                continue

            assert (
                field_model_name in KB_MODEL_NAMES_ORDERED
            ), f"Unknown model type: {field_model_name}"
            TargetModel: type[KB_MODELS] = knowledge_base_models_lookup[
                field_model_name
            ]

            current_models = dict(getattr(self, field_name))
            other_models = getattr(other, field_name)
            assert isinstance(current_models, dict)
            assert isinstance(other_models, dict)

            for key, value in other_models.items():
                if key in current_models:
                    pass  # or raise warning?
                current_models[key] = (
                    value
                    if isinstance(value, TargetModel)
                    else TargetModel.model_validate(value)
                )

            setattr(self, field_name, current_models)

    def export_knowledge_base(
        self, export_dir: Path, filename: str = "knowledge_base"
    ) -> None:
        """Export the knowledge base to the specified directory in YAML format.

        Args:
            kb (KnowledgeBase): The knowledge base to export.
            export_dir (Path): The directory to export the knowledge base to.
        """
        dump = self.ddict
        export_path = export_dir / f"{filename}.yaml"

        with open(export_path, "w", encoding="utf-8") as f:
            yaml.dump(dump, f)
