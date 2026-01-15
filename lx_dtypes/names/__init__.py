from enum import Enum
from typing import Dict, List, Literal, Optional

GENDER_OPTIONS_LITERAL = Literal["female", "male", "other", "unknown"]
GENDER_CHOICES: Dict[GENDER_OPTIONS_LITERAL, str] = {
    "female": "Female",
    "male": "Male",
    "other": "Other",
    "unknown": "Unknown",
}


# Prefix FN is for field names
NumericDistributionChoices = Enum(
    "NumericDistributionChoices",
    {
        "NORMAL": "normal",
        "LOG_NORMAL": "log_normal",
        "UNIFORM": "uniform",
        "EXPONENTIAL": "exponential",
        "UNKNOWN": "unknown",
    },
)
ClassificationChoiceDescriptorTypes = Enum(
    "ClassificationChoiceDescriptorTypes",
    {
        "NUMERIC": "numeric",
        "TEXT": "text",
        "BOOLEAN": "boolean",
        "SELECTION": "selection",
    },
)
FieldNames = Enum(
    "FieldNames",
    {
        "NAME": "name",
        "NAME_DE": "name_de",
        "NAME_EN": "name_en",
        "DESCRIPTION": "description",
        "TAGS": "tags",
        "UUID": "uuid",
        "INDICATION_TYPES": "indication_types",
        "CENTER": "center",
        "CENTERS": "centers",
        "CITATIONS": "citations",
        "CLASSIFICATION_CHOICE_DESCRIPTORS": "classification_choice_descriptors",
        "CLASSIFICATION_CHOICE_DESCRIPTOR_TYPE": "classification_choice_descriptor_type",
        "CLASSIFICATION_CHOICES": "classification_choices",
        "CLASSIFICATION": "classification",
        "CLASSIFICATIONS": "classifications",
        "CLASSIFICATION_TYPES": "classification_types",
        "FINDING": "finding",
        "FINDINGS": "findings",
        "EXAMINATION_TYPES": "examination_types",
        "EXAMINER": "examiner",
        "EXAMINERS": "examiners",
        "FINDING_TYPES": "finding_types",
        "INDICATIONS": "indications",
        "EXAMINATION": "examination",
        "EXAMINATIONS": "examinations",
        "INTERVENTION": "intervention",
        "INTERVENTIONS": "interventions",
        "INTERVENTION_TYPES": "intervention_types",
        "INFORMATION_SOURCES": "information_sources",
        "INFORMATION_SOURCE_TYPES": "information_source_types",
        "SELECTION_OPTIONS": "selection_options",
        "UNIT_TYPES": "unit_types",
        "UNIT": "unit",
        "UNITS": "units",
        #
        "PATIENT_FINDINGS": "patient_findings",
        "PATIENT_INDICATIONS": "patient_indications",
        "PATIENT_EXAMINATIONS": "patient_examinations",
        "PATIENT_FINDING_CLASSIFICATIONS": "patient_finding_classifications",
        "PATIENT_FINDING_CLASSIFICATION_CHOICES": "patient_finding_classification_choices",
        "PATIENT_FINDING_CLASSIFICATION_CHOICE_DESCRIPTORS": "patient_finding_classification_choice_descriptors",
        "PATIENT_FINDING_INTERVENTIONS": "patient_finding_interventions",
        "PATIENT_FINDING_INTERVENTION": "patient_finding_intervention",
        "PATIENTS": "patients",
    },
)


# ABM: AppBaseModel
ABM_UUID_TAGS_MODEL_LIST_TYPE_FIELDS: List[str] = [
    FieldNames.TAGS.value,
]
# KBBM = KnowledgeBaseBaseModel
KBBM_LIST_TYPE_FIELDS: List[str] = ABM_UUID_TAGS_MODEL_LIST_TYPE_FIELDS + []
LBM_LIST_TYPE_FIELDS: List[str] = ABM_UUID_TAGS_MODEL_LIST_TYPE_FIELDS + []


def mk_lbm_list_type_fields(
    new_names: Optional[List[str]] = None, m2m_fields: Optional[List[str]] = None
) -> List[str]:
    if not new_names:
        new_names = []
    base = LBM_LIST_TYPE_FIELDS.copy()
    if m2m_fields:
        new = list(set(base + m2m_fields + new_names))
    else:
        new = list(set(base + new_names))

    return new


def mk_kbbm_list_type_fields(
    new_names: Optional[List[str]] = None, m2m_fields: Optional[List[str]] = None
) -> List[str]:
    if not new_names:
        new_names = []
    base = KBBM_LIST_TYPE_FIELDS.copy()
    if m2m_fields:
        new = list(set(base + m2m_fields + new_names))
    else:
        new = list(set(base + new_names))

    return new


def rm_kbbm_list_type_fields(names: List[str]) -> List[str]:
    drop_names = mk_kbbm_list_type_fields()

    return [n for n in names if n not in drop_names]


## LEDGER BASE MODELS LIST TYPE FIELDS
CENTER_MODEL_M2M_FIELDS: List[str] = []
CENTER_MODEL_LIST_TYPE_FIELDS: List[str] = mk_lbm_list_type_fields(
    m2m_fields=CENTER_MODEL_M2M_FIELDS
)
CENTER_MODEL_NESTED_FIELDS: List[str] = [
    FieldNames.EXAMINERS.value,
]

EXAMINER_MODEL_M2M_FIELDS: List[str] = []
EXAMINER_MODEL_LIST_TYPE_FIELDS: List[str] = mk_lbm_list_type_fields(
    m2m_fields=EXAMINER_MODEL_M2M_FIELDS
)

P_EXAMINATION_MODEL_M2M_FIELDS: List[str] = []
P_EXAMINATION_MODEL_LIST_TYPE_FIELDS: List[str] = mk_lbm_list_type_fields(
    m2m_fields=P_EXAMINATION_MODEL_M2M_FIELDS
)
P_EXAMINATION_MODEL_NESTED_FIELDS: List[str] = [
    FieldNames.PATIENT_FINDINGS.value,
    FieldNames.PATIENT_INDICATIONS.value,
]

P_INDICATION_MODEL_M2M_FIELDS: List[str] = []
P_INDICATION_MODEL_LIST_TYPE_FIELDS: List[str] = mk_lbm_list_type_fields(
    m2m_fields=P_INDICATION_MODEL_M2M_FIELDS
)
P_INDICATION_MODEL_NESTED_FIELDS: List[str] = []

P_FINDING_MODEL_M2M_FIELDS: List[str] = []
P_FINDING_MODEL_LIST_TYPE_FIELDS: List[str] = mk_lbm_list_type_fields(
    m2m_fields=P_FINDING_MODEL_M2M_FIELDS
)

P_FINDING_MODEL_NESTED_FIELDS: List[str] = [
    FieldNames.PATIENT_FINDING_CLASSIFICATIONS.value,
    FieldNames.PATIENT_FINDING_INTERVENTIONS.value,
]

P_FINDING_CLASSIFICATIONS_MODEL_M2M_FIELDS: List[str] = []
P_FINDING_CLASSIFICATIONS_MODEL_LIST_TYPE_FIELDS: List[str] = mk_lbm_list_type_fields(
    m2m_fields=P_FINDING_CLASSIFICATIONS_MODEL_M2M_FIELDS
)

P_FINDING_CLASSIFICATIONS_MODEL_NESTED_FIELDS: List[str] = [
    FieldNames.PATIENT_FINDING_CLASSIFICATION_CHOICES.value,
]

P_FINDING_CLASSIFICATION_CHOICE_MODEL_M2M_FIELDS: List[str] = []
P_FINDING_CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS: List[str] = (
    mk_lbm_list_type_fields(m2m_fields=P_FINDING_CLASSIFICATION_CHOICE_MODEL_M2M_FIELDS)
)
P_FINDING_CLASSIFICATION_CHOICE_MODEL_NESTED_FIELDS: List[str] = [
    FieldNames.PATIENT_FINDING_CLASSIFICATION_CHOICE_DESCRIPTORS.value,
]

P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_M2M_FIELDS: List[str] = []
P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS: List[str] = (
    mk_lbm_list_type_fields(
        m2m_fields=P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_M2M_FIELDS
    )
)
P_FINDING_CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_NESTED_FIELDS: List[str] = []

P_INTERVENTIONS_MODEL_M2M_FIELDS: List[str] = []
P_INTERVENTIONS_MODEL_LIST_TYPE_FIELDS: List[str] = mk_lbm_list_type_fields(
    m2m_fields=P_INTERVENTIONS_MODEL_M2M_FIELDS
)
P_INTERVENTIONS_MODEL_NESTED_FIELDS: List[str] = [
    FieldNames.PATIENT_FINDING_INTERVENTIONS.value,
]

P_INTERVENTION_MODEL_M2M_FIELDS: List[str] = []
P_INTERVENTION_MODEL_LIST_TYPE_FIELDS: List[str] = mk_lbm_list_type_fields(
    m2m_fields=P_INTERVENTION_MODEL_M2M_FIELDS
)
P_INTERVENTION_MODEL_NESTED_FIELDS: List[str] = []
PATIENT_MODEL_M2M_FIELDS: List[str] = []
PATIENT_MODEL_LIST_TYPE_FIELDS: List[str] = mk_lbm_list_type_fields(
    m2m_fields=PATIENT_MODEL_M2M_FIELDS
)
PATIENT_MODEL_NESTED_FIELDS: List[str] = []
## KNOWLEDGE BASE MODELS LIST TYPE FIELDS
CITATION_MODEL_M2M_FIELDS: List[str] = []
CITATION_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    ["keywords", "authors"], m2m_fields=CITATION_MODEL_M2M_FIELDS
)
CLASSIFICATION_TYPE_M2M_FIELDS: List[str] = []
CLASSIFICATION_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    m2m_fields=CLASSIFICATION_TYPE_M2M_FIELDS
)
CLASSIFICATION_MODEL_M2M_FIELDS: List[str] = [
    FieldNames.CLASSIFICATION_CHOICES.value,
    FieldNames.CLASSIFICATION_TYPES.value,
]
CLASSIFICATION_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    m2m_fields=CLASSIFICATION_MODEL_M2M_FIELDS
)

CLASSIFICATION_CHOICE_M2M_FIELDS: List[str] = [
    FieldNames.CLASSIFICATION_CHOICE_DESCRIPTORS.value,
]
CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    m2m_fields=CLASSIFICATION_CHOICE_M2M_FIELDS
)


CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_M2M_FIELDS: List[str] = []
CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS: List[str] = (
    mk_kbbm_list_type_fields(
        [
            FieldNames.SELECTION_OPTIONS.value,
        ],
        m2m_fields=CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_M2M_FIELDS,
    )
)

FINDING_M2M_FIELDS: List[str] = [
    FieldNames.FINDING_TYPES.value,
    FieldNames.CLASSIFICATIONS.value,
    FieldNames.INTERVENTIONS.value,
]
FINDING_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(m2m_fields=FINDING_M2M_FIELDS)

FINDING_TYPE_M2M_FIELDS: List[str] = []

FINDING_TYPE_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    m2m_fields=FINDING_TYPE_M2M_FIELDS
)

EXAMINATION_M2M_FIELDS: List[str] = [
    FieldNames.FINDINGS.value,
    FieldNames.EXAMINATION_TYPES.value,
    FieldNames.INDICATIONS.value,
]
EXAMINATION_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    m2m_fields=EXAMINATION_M2M_FIELDS
)

EXAMINATION_TYPE_M2M_FIELDS: List[str] = []
EXAMINATION_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    m2m_fields=EXAMINATION_TYPE_M2M_FIELDS
)

INDICATION_M2M_FIELDS: List[str] = [
    FieldNames.INDICATION_TYPES.value,
    FieldNames.INTERVENTIONS.value,
]
INDICATION_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    m2m_fields=INDICATION_M2M_FIELDS
)

INDICATION_TYPE_M2M_FIELDS: List[str] = []
INDICATION_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    m2m_fields=INDICATION_TYPE_M2M_FIELDS
)
INTERVENTION_MODEL_M2M_FIELDS: List[str] = [
    FieldNames.INTERVENTION_TYPES.value,
]
INTERVENTION_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    m2m_fields=INTERVENTION_MODEL_M2M_FIELDS
)

INTERVENTION_TYPE_M2M_FIELDS: List[str] = []
INTERVENTION_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    m2m_fields=INTERVENTION_TYPE_M2M_FIELDS
)

INFORMATION_SOURCE_M2M_FIELDS: List[str] = [
    FieldNames.INFORMATION_SOURCE_TYPES.value,
]
INFORMATION_SOURCE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    m2m_fields=INFORMATION_SOURCE_M2M_FIELDS
)

INFORMATION_SOURCE_TYPE_M2M_FIELDS: List[str] = []
INFORMATION_SOURCE_TYPE_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    m2m_fields=INFORMATION_SOURCE_TYPE_M2M_FIELDS
)


UNIT_TYPE_M2M_FIELDS: List[str] = []
UNIT_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    m2m_fields=UNIT_TYPE_M2M_FIELDS
)

UNIT_MODEL_M2M_FIELDS: List[str] = [
    FieldNames.UNIT_TYPES.value,
]
UNIT_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(m2m_fields=UNIT_MODEL_M2M_FIELDS)
