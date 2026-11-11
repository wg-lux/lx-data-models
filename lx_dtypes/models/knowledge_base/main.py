from typing import TypeAlias, Union

from lx_dtypes.models.knowledge_base.fhir.terminology import (
    DEFAULT_FHIR_BASE_URL,
    DEFAULT_FHIR_PUBLISHER,
    FHIR_EXPORT_DOMAINS,
    export_fhir_terminology,
    export_fhir_terminology_bundle,
    import_fhir_terminology,
)
from lx_dtypes.models.knowledge_base.fhir.yaml import (
    fhir_to_yaml,
    knowledge_base_from_fhir,
    write_fhir_yaml,
)

from .citation import (
    KbCitationDjangoLookupType,
    kb_citation_django_lookup,
    kb_citation_django_models,
)
from .classification import (
    KbClassificationDjangoLookupType,
    kb_classification_django_lookup,
    kb_classification_django_models,
)
from .classification_choice import (
    KbClassificationChoiceDjangoLookupType,
    kb_classification_choice_django_lookup,
    kb_classification_choice_django_models,
)
from .classification_choice_descriptor import (
    KbClassificationChoiceDescriptorDjangoLookupType,
    kb_classification_choice_descriptor_django_lookup,
    kb_classification_choice_descriptor_django_models,
)
from .examination import (
    KbExaminationDjangoLookupType,
    kb_examination_django_lookup,
    kb_examination_django_models,
)
from .finding import (
    KbFindingDjangoLookupType,
    kb_finding_django_lookup,
    kb_finding_django_models,
)
from .indication import (
    KbIndicationDjangoLookupType,
    kb_indication_django_lookup,
    kb_indication_django_models,
)
from .information_source import (
    KbInformationSourceDjangoLookupType,
    kb_information_source_django_lookup,
    kb_information_source_django_models,
)
from .intervention import (
    KbInterventionDjangoLookupType,
    kb_intervention_django_lookup,
    kb_intervention_django_models,
)
from .pydantic_main import (
    KB_DDICTS,
    KB_MODEL_NAMES_LITERAL,
    KB_MODEL_NAMES_ORDERED,
    KB_MODELS,
    KnowledgeBaseModelsLookupType,
    knowledge_base_models_lookup,
)
from .unit import (
    KbUnitDjangoLookupType,
    kb_unit_django_lookup,
    kb_unit_django_models,
)


class KnowledgeBaseModelsDjangoLookupType(
    KbCitationDjangoLookupType,
    KbInterventionDjangoLookupType,
    KbIndicationDjangoLookupType,
    KbUnitDjangoLookupType,
    KbClassificationChoiceDescriptorDjangoLookupType,
    KbClassificationChoiceDjangoLookupType,
    KbClassificationDjangoLookupType,
    KbFindingDjangoLookupType,
    KbExaminationDjangoLookupType,
    KbInformationSourceDjangoLookupType,
):
    pass


knowledge_base_models_django_lookup: KnowledgeBaseModelsDjangoLookupType = (
    KnowledgeBaseModelsDjangoLookupType(
        **kb_citation_django_lookup,
        **kb_intervention_django_lookup,
        **kb_indication_django_lookup,
        **kb_unit_django_lookup,
        **kb_classification_choice_descriptor_django_lookup,
        **kb_classification_choice_django_lookup,
        **kb_classification_django_lookup,
        **kb_finding_django_lookup,
        **kb_examination_django_lookup,
        **kb_information_source_django_lookup,
    )
)


KB_MODELS_DJANGO: TypeAlias = Union[
    kb_citation_django_models,
    kb_intervention_django_models,
    kb_indication_django_models,
    kb_unit_django_models,
    kb_classification_choice_descriptor_django_models,
    kb_classification_choice_django_models,
    kb_classification_django_models,
    kb_finding_django_models,
    kb_examination_django_models,
    kb_information_source_django_models,
]


__all__ = [
    "DEFAULT_FHIR_BASE_URL",
    "DEFAULT_FHIR_PUBLISHER",
    "FHIR_EXPORT_DOMAINS",
    "KB_DDICTS",
    "KB_MODELS",
    "KB_MODELS_DJANGO",
    "KB_MODEL_NAMES_LITERAL",
    "KB_MODEL_NAMES_ORDERED",
    "KnowledgeBaseModelsDjangoLookupType",
    "KnowledgeBaseModelsLookupType",
    "export_fhir_terminology",
    "export_fhir_terminology_bundle",
    "fhir_to_yaml",
    "import_fhir_terminology",
    "knowledge_base_from_fhir",
    "knowledge_base_models_django_lookup",
    "knowledge_base_models_lookup",
    "write_fhir_yaml",
]
