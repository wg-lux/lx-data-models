from typing import Dict

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base.classification.Classification import (
    Classification,
)
from lx_dtypes.models.knowledge_base.classification.ClassificationType import (
    ClassificationType,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.examination.Examination import Examination
from lx_dtypes.models.knowledge_base.examination.ExaminationType import ExaminationType
from lx_dtypes.models.knowledge_base.finding.Finding import Finding
from lx_dtypes.models.knowledge_base.finding.FindingType import FindingType
from lx_dtypes.models.knowledge_base.indication.Indication import Indication
from lx_dtypes.models.knowledge_base.indication.IndicationType import IndicationType
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.intervention.InterventionType import (
    InterventionType,
)
from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitType import UnitType


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

    # TODO
    # @classmethod
    # def create_from_config(cls, config: "KnowledgeBaseConfig") -> "KnowledgeBase":
    #     source_file = config.source_file
    #     # assert source_file is not None, "Config must have source_file set." # Can be removed?
    #     kb_source_dict: Dict[str, Union["KnowledgeBaseConfig", Path]] = {
    #         "config": config,
    #         # "source_file": source_file, # Can be removed?
    #     }
    #     kb = cls.model_validate(kb_source_dict)
    #     data = config.data
    #     submodule_files = data.get_files_with_suffix(".yaml")
    #     # for sm_file in submodule_files:

    #     # parsed_object_generator = parse_shallow_object(sm_file, kb_module_name=name)
    #     # for parsed_object in parsed_object_generator:
