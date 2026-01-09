from typing import List, Literal, Union

from .citation import (
    KbCitationDjangoLookupType,
    KbCitationLookupType,
    kb_citation_ddicts,
    kb_citation_django,
    kb_citation_django_lookup,
    kb_citation_lookup,
    kb_citation_models,
)
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
    KbIndicationDjangoLookupType,
    KbIndicationLookupType,
    kb_indication_ddicts,
    kb_indication_django_lookup,
    kb_indication_django_models,
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
    KbInterventionDjangoLookupType,
    KbInterventionLookupType,
    kb_intervention_ddicts,
    kb_intervention_django_lookup,
    kb_intervention_django_models,
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
    KbCitationLookupType,
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
    **kb_citation_lookup,
)


class KnowledgeBaseModelsDjangoLookupType(
    KbCitationDjangoLookupType,
    KbInterventionDjangoLookupType,
    KbIndicationDjangoLookupType,
):
    pass


knowledge_base_models_django_lookup = KnowledgeBaseModelsDjangoLookupType(
    **kb_citation_django_lookup,
    **kb_intervention_django_lookup,
    **kb_indication_django_lookup,
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
    kb_citation_models,
]

KB_MODELS_DJANGO = Union[
    kb_citation_django,
    kb_intervention_django_models,
    kb_indication_django_models,
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
    kb_citation_ddicts,
]

KB_MODEL_NAMES_LITERAL = Literal[
    "UnitType",
    "Unit",
    "ClassificationChoiceDescriptor",
    "ClassificationChoice",
    "ClassificationType",
    "Classification",
    "Citation",
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
    "Citation",
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
