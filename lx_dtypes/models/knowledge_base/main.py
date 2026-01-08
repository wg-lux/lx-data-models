from typing import List, Literal, Union

from .classification import (
    KbClassificationLookupType,
    kb_classification_ddicts,
    kb_classification_lookup,
    kb_classification_models,
)
from .classification_choice import (
    KbClassificationChoiceLookupType,
    kb_classification_choice_ddicts,
    kb_classification_choice_lookup,
    kb_classification_choice_models,
)
from .classification_choice_descriptor import (
    KbClassificationChoiceDescriptorLookupType,
    kb_classification_choice_descriptor_ddicts,
    kb_classification_choice_descriptor_lookup,
    kb_classification_choice_descriptor_models,
)
from .examination import (
    KbExaminationLookupType,
    kb_examination_ddicts,
    kb_examination_lookup,
    kb_examination_models,
)
from .finding import (
    KbFindingLookupType,
    kb_finding_ddicts,
    kb_finding_lookup,
    kb_finding_models,
)
from .indication import (
    KbIndicationLookupType,
    kb_indication_ddicts,
    kb_indication_lookup,
    kb_indication_models,
)
from .information_source import (
    KbInformationSourceLookupType,
    kb_information_source_ddicts,
    kb_information_source_lookup,
    kb_information_source_models,
)
from .intervention import (
    KbInterventionLookupType,
    kb_intervention_ddicts,
    kb_intervention_lookup,
    kb_intervention_models,
)
from .unit import KbUnitLookupType, kb_unit_ddicts, kb_unit_lookup, kb_unit_models


class KnowledgeBaseModelsLookupType(
    KbClassificationLookupType,
    KbClassificationChoiceLookupType,
    KbClassificationChoiceDescriptorLookupType,
    KbExaminationLookupType,
    KbFindingLookupType,
    KbIndicationLookupType,
    KbInterventionLookupType,
    KbUnitLookupType,
    KbInformationSourceLookupType,
):
    pass


knowledge_base_models_lookup = KnowledgeBaseModelsLookupType(
    **kb_classification_lookup,
    **kb_classification_choice_lookup,
    **kb_classification_choice_descriptor_lookup,
    **kb_examination_lookup,
    **kb_finding_lookup,
    **kb_indication_lookup,
    **kb_intervention_lookup,
    **kb_unit_lookup,
    **kb_information_source_lookup,
)

KB_MODELS = Union[
    kb_classification_models,
    kb_classification_choice_models,
    kb_classification_choice_descriptor_models,
    kb_examination_models,
    kb_finding_models,
    kb_indication_models,
    kb_intervention_models,
    kb_unit_models,
    kb_information_source_models,
]

KB_DDICTS = Union[
    kb_classification_ddicts,
    kb_classification_choice_ddicts,
    kb_classification_choice_descriptor_ddicts,
    kb_examination_ddicts,
    kb_finding_ddicts,
    kb_indication_ddicts,
    kb_intervention_ddicts,
    kb_unit_ddicts,
    kb_information_source_ddicts,
]

KB_MODEL_NAMES_LITERAL = Literal[
    "UnitType",
    "Unit",
    "ClassificationChoiceDescriptor",
    "ClassificationChoice",
    "ClassificationType",
    "Classification",
    "InterventionType",
    "Intervention",
    "FindingType",
    "Finding",
    "IndicationType",
    "Indication",
    "ExaminationType",
    "Examination",
    "InformationSourceType",
    "InformationSource",
]

KB_MODEL_NAMES_ORDERED: List[KB_MODEL_NAMES_LITERAL] = [
    "InformationSourceType",
    "InformationSource",
    "UnitType",
    "Unit",
    "ClassificationChoiceDescriptor",
    "ClassificationChoice",
    "ClassificationType",
    "Classification",
    "InterventionType",
    "Intervention",
    "FindingType",
    "Finding",
    "IndicationType",
    "Indication",
    "ExaminationType",
    "Examination",
]
