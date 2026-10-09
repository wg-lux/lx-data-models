from typing import Literal, TypeAlias, Union

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

from .center.center_employee_list import (
    CenterEmployeeList,
    CenterEmployeeListDataDict,
    KbCenterEmployeeListLookupType,
)
from .citation import (
    KbCitationDjangoLookupType,
    KbCitationLookupType,
    kb_citation_ddicts,
    kb_citation_django_lookup,
    kb_citation_django_models,
    kb_citation_lookup,
    kb_citation_models,
)
from .classification import (
    KbClassificationDjangoLookupType,
    KbClassificationLookupType,
    kb_classification_ddicts,
    kb_classification_django_lookup,
    kb_classification_django_models,
    kb_classification_lookup,
    kb_classification_models,
)
from .classification_choice import (
    KbClassificationChoiceDjangoLookupType,
    KbClassificationChoiceLookupType,
    kb_classification_choice_ddicts,
    kb_classification_choice_django_lookup,
    kb_classification_choice_django_models,
    kb_classification_choice_lookup,
    kb_classification_choice_models,
)
from .classification_choice_descriptor import (
    KbClassificationChoiceDescriptorDjangoLookupType,
    KbClassificationChoiceDescriptorLookupType,
    kb_classification_choice_descriptor_ddicts,
    kb_classification_choice_descriptor_django_lookup,
    kb_classification_choice_descriptor_django_models,
    kb_classification_choice_descriptor_lookup,
    kb_classification_choice_descriptor_models,
)
from .examination import (
    KbExaminationDjangoLookupType,
    KbExaminationLookupType,
    kb_examination_ddicts,
    kb_examination_django_lookup,
    kb_examination_django_models,
    kb_examination_lookup,
    kb_examination_models,
)
from .finding import (
    KbFindingDjangoLookupType,
    KbFindingLookupType,
    kb_finding_ddicts,
    kb_finding_django_lookup,
    kb_finding_django_models,
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
    KbInformationSourceDjangoLookupType,
    KbInformationSourceLookupType,
    kb_information_source_ddicts,
    kb_information_source_django_lookup,
    kb_information_source_django_models,
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
from .reference_catalog import (
    KbReferenceCatalogLookupType,
    ReferenceCatalog,
    ReferenceCatalogDataDict,
)
from .report_template import (
    KbReportTemplateLookupType,
    kb_report_template_ddicts,
    kb_report_template_lookup,
    kb_report_template_models,
)
from .study_preset import KbStudyPresetLookupType, StudyPreset, StudyPresetDataDict
from .unit import (
    KbUnitDjangoLookupType,
    KbUnitLookupType,
    kb_unit_ddicts,
    kb_unit_django_lookup,
    kb_unit_django_models,
    kb_unit_lookup,
    kb_unit_models,
)


class KnowledgeBaseModelsLookupType(
    KbCenterEmployeeListLookupType,
    KbStudyPresetLookupType,
    KbReferenceCatalogLookupType,
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
    KbReportTemplateLookupType,
):
    pass


knowledge_base_models_lookup = KnowledgeBaseModelsLookupType(
    CenterEmployeeList=CenterEmployeeList,
    StudyPreset=StudyPreset,
    ReferenceCatalog=ReferenceCatalog,
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
    **kb_report_template_lookup,
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

KB_MODELS: TypeAlias = Union[
    StudyPreset,
    ReferenceCatalog,
    CenterEmployeeList,
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
    kb_report_template_models,
]

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

KB_DDICTS: TypeAlias = Union[
    StudyPresetDataDict,
    ReferenceCatalogDataDict,
    CenterEmployeeListDataDict,
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
    kb_report_template_ddicts,
]

KB_MODEL_NAMES_LITERAL = Literal[
    "CenterEmployeeList",
    "StudyPreset",
    "ReferenceCatalog",
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
    "ReportTemplateSection",
    "ReportFinding",
    "ClassificationValidator",
    "InterventionValidator",
    "UnitValidator",
    "FindingsValidator",
    "ExaminationValidator",
    "ReportTemplate",
]

KB_MODEL_NAMES_ORDERED: list[KB_MODEL_NAMES_LITERAL] = [
    "CenterEmployeeList",
    "StudyPreset",
    "ReferenceCatalog",
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
    "ReportTemplateSection",
    "ReportFinding",
    "ClassificationValidator",
    "InterventionValidator",
    "UnitValidator",
    "FindingsValidator",
    "ExaminationValidator",
    "ReportTemplate",
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
