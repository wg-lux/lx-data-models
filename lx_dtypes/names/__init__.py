from enum import Enum
from typing import List, Optional

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
        "CLASSIFICATION_CHOICE_DESCRIPTORS": "classification_choice_descriptors",
        "CLASSIFICATION_CHOICE_DESCRIPTOR_TYPE": "classification_choice_descriptor_type",
        "CLASSIFICATION_CHOICES": "classification_choices",
        "CLASSIFICATION": "classification",
        "CLASSIFICATIONS": "classifications",
        "CLASSIFICATION_TYPES": "classification_types",
        "FINDING": "finding",
        "FINDINGS": "findings",
        "EXAMINATION_TYPES": "examination_types",
        "FINDING_TYPES": "finding_types",
        "INDICATIONS": "indications",
        "EXAMINATION": "examination",
        "INTERVENTION": "intervention",
        "INTERVENTIONS": "interventions",
        "INTERVENTION_TYPES": "intervention_types",
        "SELECTION_OPTIONS": "selection_options",
        "UNIT_TYPES": "unit_types",
        "UNIT": "unit",
    },
)


# ABM: AppBaseModel
ABM_UUID_TAGS_MODEL_LIST_TYPE_FIELDS: List[str] = [
    FieldNames.TAGS.value,
]
# KBBM = KnowledgeBaseBaseModel
KBBM_LIST_TYPE_FIELDS: List[str] = ABM_UUID_TAGS_MODEL_LIST_TYPE_FIELDS + []


def mk_kbbm_list_type_fields(new_names: Optional[List[str]] = None) -> List[str]:
    if not new_names:
        new_names = []
    base = KBBM_LIST_TYPE_FIELDS.copy()
    new = list(set(base + new_names))

    return new


CLASSIFICATION_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields()
CLASSIFICATION_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    [
        FieldNames.CLASSIFICATION_CHOICES.value,
        FieldNames.CLASSIFICATION_TYPES.value,
    ]
)

CLASSIFICATION_CHOICE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields(
    [
        FieldNames.CLASSIFICATION_CHOICE_DESCRIPTORS.value,
    ]
)

CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS: List[str] = (
    mk_kbbm_list_type_fields(
        [
            FieldNames.SELECTION_OPTIONS.value,
        ]
    )
)

FINDING_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    [
        FieldNames.FINDING_TYPES.value,
        FieldNames.CLASSIFICATIONS.value,
        FieldNames.INTERVENTIONS.value,
    ]
)

FINDING_TYPE_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields()

EXAMINATION_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    [
        FieldNames.FINDINGS.value,
        FieldNames.EXAMINATION_TYPES.value,
        FieldNames.INDICATIONS.value,
    ]
)

EXAMINATION_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields()

INDICATION_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    [
        FieldNames.INDICATION_TYPES.value,
        FieldNames.INTERVENTIONS.value,
    ]
)

INDICATION_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields()

INTERVENTION_MODEL_LIST_TYPE_FIELDS = mk_kbbm_list_type_fields(
    [
        FieldNames.INTERVENTION_TYPES.value,
    ]
)

INTERVENTION_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields()

UNIT_TYPE_MODEL_LIST_TYPE_FIELDS: List[str] = mk_kbbm_list_type_fields()
UNIT_MODEL_LIST_TYPE_FIELDS = [
    FieldNames.UNIT_TYPES.value,
]
