"""Versioned, typed reference-catalog records for lossless host provisioning.

These are reference definitions only. Patient records, employee names, model
weights and active-model selection are deliberately outside this contract.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date, time
from enum import StrEnum
from typing import Annotated, ClassVar, Literal, Self, cast

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from lx_dtypes.models.contracts.lab_value import LabValueNormalRangeData
from lx_dtypes.models.contracts.reference_metadata import (
    ClassificationNumericalDescriptorDefinition,
    ClassificationSubcategoryDefinition,
)


def _date(value: object) -> object:
    return date.fromisoformat(value) if isinstance(value, str) else value


def _time(value: object) -> object:
    return time.fromisoformat(value) if isinstance(value, str) else value


CatalogDate = Annotated[date, BeforeValidator(_date)]
CatalogTime = Annotated[time, BeforeValidator(_time)]


class ReferenceKind(StrEnum):
    AI_MODEL = "ai_model"
    CENTER = "center"
    CONTRAINDICATION = "contraindication"
    DATE_VALUE_DISTRIBUTION = "date_value_distribution"
    DISEASE = "disease"
    DISEASE_CLASSIFICATION = "disease_classification"
    DISEASE_CLASSIFICATION_CHOICE = "disease_classification_choice"
    ENDOSCOPE = "endoscope"
    ENDOSCOPE_TYPE = "endoscope_type"
    ENDOSCOPY_PROCESSOR = "endoscopy_processor"
    EVENT = "event"
    EXAMINATION = "examination"
    EXAMINATION_INDICATION = "examination_indication"
    EXAMINATION_INDICATION_CLASSIFICATION = "examination_indication_classification"
    EXAMINATION_INDICATION_CLASSIFICATION_CHOICE = (
        "examination_indication_classification_choice"
    )
    EXAMINATION_TIME = "examination_time"
    EXAMINATION_TIME_TYPE = "examination_time_type"
    EXAMINATION_TYPE = "examination_type"
    FINDING = "finding"
    FINDING_CLASSIFICATION = "finding_classification"
    FINDING_CLASSIFICATION_CHOICE = "finding_classification_choice"
    FINDING_CLASSIFICATION_TYPE = "finding_classification_type"
    FINDING_INTERVENTION = "finding_intervention"
    FINDING_INTERVENTION_TYPE = "finding_intervention_type"
    FINDING_TYPE = "finding_type"
    GENDER = "gender"
    INFORMATION_SOURCE = "information_source"
    INFORMATION_SOURCE_TYPE = "information_source_type"
    LAB_VALUE = "lab_value"
    LABEL = "label"
    LABEL_SET = "label_set"
    LABEL_TYPE = "label_type"
    MEDICATION = "medication"
    MEDICATION_INDICATION = "medication_indication"
    MEDICATION_INDICATION_TYPE = "medication_indication_type"
    MEDICATION_INTAKE_TIME = "medication_intake_time"
    MEDICATION_SCHEDULE = "medication_schedule"
    MODEL_TYPE = "model_type"
    MULTIPLE_CATEGORICAL_VALUE_DISTRIBUTION = "multiple_categorical_value_distribution"
    NUMERIC_VALUE_DISTRIBUTION = "numeric_value_distribution"
    ORGAN = "organ"
    PATIENT_LAB_SAMPLE_TYPE = "patient_lab_sample_type"
    PDF_TYPE = "pdf_type"
    REPORT_READER_FLAG = "report_reader_flag"
    RISK = "risk"
    RISK_TYPE = "risk_type"
    SINGLE_CATEGORICAL_VALUE_DISTRIBUTION = "single_categorical_value_distribution"
    TAG = "tag"
    UNIT = "unit"
    VIDEO_SEGMENTATION_LABEL = "video_segmentation_label"
    VIDEO_SEGMENTATION_LABEL_SET = "video_segmentation_label_set"
    CENTER_RESOURCE = "center_resource"
    CENTER_WASTE = "center_waste"
    EMISSION_FACTOR = "emission_factor"
    MATERIAL = "material"
    PRODUCT = "product"
    PRODUCT_GROUP = "product_group"
    PRODUCT_MATERIAL = "product_material"
    PRODUCT_WEIGHT = "product_weight"
    PROFESSION = "profession"
    QUALIFICATION = "qualification"
    QUALIFICATION_TYPE = "qualification_type"
    REFERENCE_PRODUCT = "reference_product"
    RESOURCE = "resource"
    SHIFT = "shift"
    SHIFT_TYPE = "shift_type"
    TRANSPORT_ROUTE = "transport_route"
    WASTE = "waste"


class CatalogIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    name: str = Field(min_length=1)
    version: int | None = None


class CatalogRecordBase(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    identity_fields: ClassVar[tuple[str, ...]] = ()
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {}
    many_relations: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def normalize_relations(self) -> Self:
        for field in self.many_relations:
            identities = [
                identity for name, _, identity in self.references() if name == field
            ]
            if len(identities) != len(set(identities)):
                raise ValueError(
                    f"Duplicate reference in {self.kind}.{self.identity.name}.{field}"
                )
            setattr(
                self,
                field,
                sorted(
                    identities,
                    key=lambda identity: (identity.name, identity.version or 0),
                ),
            )
        return self

    @property
    def kind(self) -> ReferenceKind:
        value: object = self.record_type
        if not isinstance(value, str):
            raise TypeError("Catalog discriminator must be a string")
        return ReferenceKind(value)

    @property
    def identity(self) -> CatalogIdentity:
        version: object = getattr(self, "version", None)
        if version is not None and (
            not isinstance(version, int) or isinstance(version, bool)
        ):
            raise TypeError("Reference record version must be an integer")
        name: object = getattr(self, "name", None)
        if isinstance(name, str) and name:
            return CatalogIdentity(name=name, version=version)
        if not self.identity_fields:
            raise ValueError(
                "Reference records require a name or a declared composite identity"
            )
        fields = self.model_dump(
            mode="json", by_alias=True, include=set(self.identity_fields)
        )
        if set(fields) != set(self.identity_fields) or any(
            value is None for value in fields.values()
        ):
            raise ValueError("Composite reference identity fields must all be present")
        return CatalogIdentity(
            name=json.dumps(
                fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ),
            version=version,
        )

    @property
    def key(self) -> tuple[ReferenceKind, str, int | None]:
        return self.kind, self.identity.name, self.identity.version

    def references(self) -> Iterator[tuple[str, ReferenceKind, CatalogIdentity]]:
        for field, target in self.relation_targets.items():
            value: object = getattr(self, field)
            if value is None:
                continue
            if isinstance(value, CatalogIdentity):
                yield field, target, value
            elif isinstance(value, list):
                for item in cast(list[object], value):
                    if not isinstance(item, CatalogIdentity):
                        raise TypeError("Invalid reference identity")
                    yield field, target, item
            else:
                raise TypeError("Invalid reference collection")


class AiModelReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.AI_MODEL] = ReferenceKind.AI_MODEL
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "model_type": ReferenceKind.MODEL_TYPE,
        "video_segmentation_labelset": ReferenceKind.VIDEO_SEGMENTATION_LABEL_SET,
    }
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    model_type: CatalogIdentity | None
    model_subtype: str | None = Field(max_length=255)
    video_segmentation_labelset: CatalogIdentity | None


class CenterReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.CENTER] = ReferenceKind.CENTER
    name: str = Field(max_length=255, min_length=1)
    center_key: str = Field(max_length=255)
    display_name: str = Field(max_length=255)


class ContraindicationReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.CONTRAINDICATION] = (
        ReferenceKind.CONTRAINDICATION
    )
    name: str = Field(max_length=100, min_length=1)
    description: str | None


class DateValueDistributionReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.DATE_VALUE_DISTRIBUTION] = (
        ReferenceKind.DATE_VALUE_DISTRIBUTION
    )
    name: str = Field(max_length=100, min_length=1)
    description: str | None
    distribution_type: Literal["uniform", "normal"]
    mode: Literal["date", "timedelta"]
    date_min: CatalogDate | None
    date_max: CatalogDate | None
    date_mean: CatalogDate | None
    date_std_dev: int | None
    timedelta_days_min: int | None
    timedelta_days_max: int | None
    timedelta_days_mean: int | None
    timedelta_days_std_dev: int | None


class DiseaseReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.DISEASE] = ReferenceKind.DISEASE
    name: str = Field(max_length=255, min_length=1)
    subcategories: dict[str, ClassificationSubcategoryDefinition]
    numerical_descriptors: dict[str, ClassificationNumericalDescriptorDefinition]


class DiseaseClassificationReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.DISEASE_CLASSIFICATION] = (
        ReferenceKind.DISEASE_CLASSIFICATION
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "disease": ReferenceKind.DISEASE
    }
    name: str = Field(max_length=255, min_length=1)
    disease: CatalogIdentity


class DiseaseClassificationChoiceReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.DISEASE_CLASSIFICATION_CHOICE] = (
        ReferenceKind.DISEASE_CLASSIFICATION_CHOICE
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "disease_classification": ReferenceKind.DISEASE_CLASSIFICATION
    }
    name: str = Field(max_length=255, min_length=1)
    disease_classification: CatalogIdentity


class EndoscopeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.ENDOSCOPE] = ReferenceKind.ENDOSCOPE
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "center": ReferenceKind.CENTER,
        "endoscope_type": ReferenceKind.ENDOSCOPE_TYPE,
    }
    name: str = Field(max_length=255, min_length=1)
    sn: str = Field(max_length=255)
    center: CatalogIdentity | None
    endoscope_type: CatalogIdentity | None


class EndoscopeTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.ENDOSCOPE_TYPE] = ReferenceKind.ENDOSCOPE_TYPE
    name: str = Field(max_length=255, min_length=1)


class EndoscopyProcessorReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.ENDOSCOPY_PROCESSOR] = (
        ReferenceKind.ENDOSCOPY_PROCESSOR
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "centers": ReferenceKind.CENTER
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(["centers"])
    name: str = Field(max_length=255, min_length=1)
    image_width: int
    image_height: int
    endoscope_image_x: int
    endoscope_image_y: int
    endoscope_image_width: int
    endoscope_image_height: int
    examination_date_x: int
    examination_date_y: int
    examination_date_width: int
    examination_date_height: int
    examination_time_x: int | None
    examination_time_y: int | None
    examination_time_width: int | None
    examination_time_height: int | None
    patient_first_name_x: int
    patient_first_name_y: int
    patient_first_name_width: int
    patient_first_name_height: int
    patient_last_name_x: int
    patient_last_name_y: int
    patient_last_name_width: int
    patient_last_name_height: int
    patient_dob_x: int
    patient_dob_y: int
    patient_dob_width: int
    patient_dob_height: int
    endoscope_type_x: int | None
    endoscope_type_y: int | None
    endoscope_type_width: int | None
    endoscope_type_height: int | None
    endoscope_sn_x: int | None
    endoscope_sn_y: int | None
    endoscope_sn_width: int | None
    endoscope_sn_height: int | None
    centers: list[CatalogIdentity]


class EventReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.EVENT] = ReferenceKind.EVENT
    name: str = Field(max_length=100, min_length=1)
    description: str | None


class ExaminationReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.EXAMINATION] = ReferenceKind.EXAMINATION
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "examination_types": ReferenceKind.EXAMINATION_TYPE,
        "indications": ReferenceKind.EXAMINATION_INDICATION,
        "examination_times": ReferenceKind.EXAMINATION_TIME,
        "findings": ReferenceKind.FINDING,
        "information_sources": ReferenceKind.INFORMATION_SOURCE,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(
        [
            "examination_types",
            "indications",
            "examination_times",
            "findings",
            "information_sources",
        ]
    )
    name: str = Field(max_length=100, min_length=1)
    description: str | None
    examination_types: list[CatalogIdentity]
    indications: list[CatalogIdentity]
    examination_times: list[CatalogIdentity]
    findings: list[CatalogIdentity]
    information_sources: list[CatalogIdentity]


class ExaminationIndicationReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.EXAMINATION_INDICATION] = (
        ReferenceKind.EXAMINATION_INDICATION
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "classifications": ReferenceKind.EXAMINATION_INDICATION_CLASSIFICATION,
        "expected_interventions": ReferenceKind.FINDING_INTERVENTION,
        "information_sources": ReferenceKind.INFORMATION_SOURCE,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(
        ["classifications", "expected_interventions", "information_sources"]
    )
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    classifications: list[CatalogIdentity]
    expected_interventions: list[CatalogIdentity]
    information_sources: list[CatalogIdentity]


class ExaminationIndicationClassificationReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.EXAMINATION_INDICATION_CLASSIFICATION] = (
        ReferenceKind.EXAMINATION_INDICATION_CLASSIFICATION
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "choices": ReferenceKind.EXAMINATION_INDICATION_CLASSIFICATION_CHOICE
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(["choices"])
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    choices: list[CatalogIdentity]


class ExaminationIndicationClassificationChoiceReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.EXAMINATION_INDICATION_CLASSIFICATION_CHOICE] = (
        ReferenceKind.EXAMINATION_INDICATION_CLASSIFICATION_CHOICE
    )
    name: str = Field(max_length=255, min_length=1)
    subcategories: dict[str, ClassificationSubcategoryDefinition]
    numerical_descriptors: dict[str, ClassificationNumericalDescriptorDefinition]


class ExaminationTimeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.EXAMINATION_TIME] = (
        ReferenceKind.EXAMINATION_TIME
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "time_types": ReferenceKind.EXAMINATION_TIME_TYPE,
        "information_sources": ReferenceKind.INFORMATION_SOURCE,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(
        ["time_types", "information_sources"]
    )
    name: str = Field(max_length=100, min_length=1)
    time_types: list[CatalogIdentity]
    information_sources: list[CatalogIdentity]


class ExaminationTimeTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.EXAMINATION_TIME_TYPE] = (
        ReferenceKind.EXAMINATION_TIME_TYPE
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "examinations": ReferenceKind.EXAMINATION
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(["examinations"])
    name: str = Field(max_length=100, min_length=1)
    examinations: list[CatalogIdentity]


class ExaminationTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.EXAMINATION_TYPE] = (
        ReferenceKind.EXAMINATION_TYPE
    )
    name: str = Field(max_length=100, min_length=1)


class FindingReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.FINDING] = ReferenceKind.FINDING
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "finding_types": ReferenceKind.FINDING_TYPE,
        "finding_interventions": ReferenceKind.FINDING_INTERVENTION,
        "caused_by_interventions": ReferenceKind.FINDING_INTERVENTION,
        "finding_classifications": ReferenceKind.FINDING_CLASSIFICATION,
        "information_sources": ReferenceKind.INFORMATION_SOURCE,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(
        [
            "finding_types",
            "finding_interventions",
            "caused_by_interventions",
            "finding_classifications",
            "information_sources",
        ]
    )
    name: str = Field(max_length=100, min_length=1)
    description: str | None
    finding_types: list[CatalogIdentity]
    finding_interventions: list[CatalogIdentity]
    caused_by_interventions: list[CatalogIdentity]
    finding_classifications: list[CatalogIdentity]
    information_sources: list[CatalogIdentity]


class FindingClassificationReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.FINDING_CLASSIFICATION] = (
        ReferenceKind.FINDING_CLASSIFICATION
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "finding_types": ReferenceKind.FINDING_TYPE,
        "choices": ReferenceKind.FINDING_CLASSIFICATION_CHOICE,
        "classification_types": ReferenceKind.FINDING_CLASSIFICATION_TYPE,
        "information_sources": ReferenceKind.INFORMATION_SOURCE,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(
        ["finding_types", "choices", "classification_types", "information_sources"]
    )
    name: str = Field(max_length=255, min_length=1)
    description: str
    finding_types: list[CatalogIdentity]
    choices: list[CatalogIdentity]
    classification_types: list[CatalogIdentity]
    information_sources: list[CatalogIdentity]


class FindingClassificationChoiceReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.FINDING_CLASSIFICATION_CHOICE] = (
        ReferenceKind.FINDING_CLASSIFICATION_CHOICE
    )
    name: str = Field(max_length=255, min_length=1)
    description: str
    subcategories: dict[str, ClassificationSubcategoryDefinition]
    numerical_descriptors: dict[str, ClassificationNumericalDescriptorDefinition]


class FindingClassificationTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.FINDING_CLASSIFICATION_TYPE] = (
        ReferenceKind.FINDING_CLASSIFICATION_TYPE
    )
    name: str = Field(max_length=255, min_length=1)
    description: str


class FindingInterventionReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.FINDING_INTERVENTION] = (
        ReferenceKind.FINDING_INTERVENTION
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "intervention_types": ReferenceKind.FINDING_INTERVENTION_TYPE,
        "information_sources": ReferenceKind.INFORMATION_SOURCE,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(
        ["intervention_types", "information_sources"]
    )
    name: str = Field(max_length=100, min_length=1)
    description: str | None
    intervention_types: list[CatalogIdentity]
    information_sources: list[CatalogIdentity]


class FindingInterventionTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.FINDING_INTERVENTION_TYPE] = (
        ReferenceKind.FINDING_INTERVENTION_TYPE
    )
    name: str = Field(max_length=100, min_length=1)
    description: str | None


class FindingTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.FINDING_TYPE] = ReferenceKind.FINDING_TYPE
    name: str = Field(max_length=100, min_length=1)
    description: str | None


class GenderReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.GENDER] = ReferenceKind.GENDER
    name: str = Field(max_length=255, min_length=1)
    abbreviation: str | None = Field(max_length=255)
    description: str | None


class InformationSourceReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.INFORMATION_SOURCE] = (
        ReferenceKind.INFORMATION_SOURCE
    )
    name: str = Field(max_length=100, min_length=1)
    url: str | None = Field(max_length=200)
    description: str | None
    date: CatalogDate | None
    abbreviation: str | None = Field(max_length=100)


class InformationSourceTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.INFORMATION_SOURCE_TYPE] = (
        ReferenceKind.INFORMATION_SOURCE_TYPE
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "information_sources": ReferenceKind.INFORMATION_SOURCE
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(["information_sources"])
    name: str = Field(max_length=100, min_length=1)
    description: str | None
    information_sources: list[CatalogIdentity]


class LabValueReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.LAB_VALUE] = ReferenceKind.LAB_VALUE
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "default_unit": ReferenceKind.UNIT,
        "default_single_categorical_value_distribution": ReferenceKind.SINGLE_CATEGORICAL_VALUE_DISTRIBUTION,
        "default_numerical_value_distribution": ReferenceKind.NUMERIC_VALUE_DISTRIBUTION,
        "default_multiple_categorical_value_distribution": ReferenceKind.MULTIPLE_CATEGORICAL_VALUE_DISTRIBUTION,
        "default_date_value_distribution": ReferenceKind.DATE_VALUE_DISTRIBUTION,
    }
    name: str = Field(max_length=255, min_length=1)
    abbreviation: str | None = Field(max_length=10)
    default_unit: CatalogIdentity | None
    numeric_precision: int
    default_single_categorical_value_distribution: CatalogIdentity | None
    default_numerical_value_distribution: CatalogIdentity | None
    default_multiple_categorical_value_distribution: CatalogIdentity | None
    default_date_value_distribution: CatalogIdentity | None
    default_normal_range: LabValueNormalRangeData | None
    normal_range_age_dependent: bool
    normal_range_gender_dependent: bool
    normal_range_special_case: bool
    bound_adjustment_factor: float


class LabelReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.LABEL] = ReferenceKind.LABEL
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "label_type": ReferenceKind.LABEL_TYPE
    }
    name: str = Field(max_length=255, min_length=1)
    label_type: CatalogIdentity | None
    description: str | None


class LabelSetReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.LABEL_SET] = ReferenceKind.LABEL_SET
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "labels": ReferenceKind.LABEL
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(["labels"])
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    version: int
    labels: list[CatalogIdentity]


class LabelTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.LABEL_TYPE] = ReferenceKind.LABEL_TYPE
    name: str = Field(max_length=255, min_length=1)
    description: str | None


class MedicationReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.MEDICATION] = ReferenceKind.MEDICATION
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "default_unit": ReferenceKind.UNIT
    }
    name: str = Field(max_length=255, min_length=1)
    adapt_to_renal_function: bool
    adapt_to_hepatic_function: bool
    adapt_to_indication: bool
    adapt_to_age: bool
    adapt_to_weight: bool
    adapt_to_risk: bool
    default_unit: CatalogIdentity


class MedicationIndicationReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.MEDICATION_INDICATION] = (
        ReferenceKind.MEDICATION_INDICATION
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "indication_type": ReferenceKind.MEDICATION_INDICATION_TYPE,
        "medication_schedules": ReferenceKind.MEDICATION_SCHEDULE,
        "diseases": ReferenceKind.DISEASE,
        "events": ReferenceKind.EVENT,
        "disease_classification_choices": ReferenceKind.DISEASE_CLASSIFICATION_CHOICE,
        "sources": ReferenceKind.INFORMATION_SOURCE,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(
        [
            "medication_schedules",
            "diseases",
            "events",
            "disease_classification_choices",
            "sources",
        ]
    )
    name: str = Field(max_length=255, min_length=1)
    indication_type: CatalogIdentity
    medication_schedules: list[CatalogIdentity]
    diseases: list[CatalogIdentity]
    events: list[CatalogIdentity]
    disease_classification_choices: list[CatalogIdentity]
    sources: list[CatalogIdentity]


class MedicationIndicationTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.MEDICATION_INDICATION_TYPE] = (
        ReferenceKind.MEDICATION_INDICATION_TYPE
    )
    name: str = Field(max_length=255, min_length=1)


class MedicationIntakeTimeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.MEDICATION_INTAKE_TIME] = (
        ReferenceKind.MEDICATION_INTAKE_TIME
    )
    name: str = Field(max_length=255, min_length=1)
    repeats: str = Field(max_length=20)
    time: CatalogTime


class MedicationScheduleReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.MEDICATION_SCHEDULE] = (
        ReferenceKind.MEDICATION_SCHEDULE
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "medication": ReferenceKind.MEDICATION,
        "unit": ReferenceKind.UNIT,
        "intake_times": ReferenceKind.MEDICATION_INTAKE_TIME,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(["intake_times"])
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    medication: CatalogIdentity
    unit: CatalogIdentity
    therapy_duration_d: float | None
    dose: float
    intake_times: list[CatalogIdentity]


class ModelTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.MODEL_TYPE] = ReferenceKind.MODEL_TYPE
    name: str = Field(max_length=255, min_length=1)
    description: str | None


class MultipleCategoricalValueDistributionReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.MULTIPLE_CATEGORICAL_VALUE_DISTRIBUTION] = (
        ReferenceKind.MULTIPLE_CATEGORICAL_VALUE_DISTRIBUTION
    )
    name: str = Field(max_length=100, min_length=1)
    categories: dict[str, float]
    min_count: int
    max_count: int
    count_distribution_type: Literal["uniform", "normal"]
    count_mean: float | None
    count_std_dev: float | None


class NumericValueDistributionReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.NUMERIC_VALUE_DISTRIBUTION] = (
        ReferenceKind.NUMERIC_VALUE_DISTRIBUTION
    )
    name: str = Field(max_length=100, min_length=1)
    distribution_type: Literal["uniform", "normal", "skewed_normal"]
    min_descriptor: str = Field(max_length=20)
    max_descriptor: str = Field(max_length=20)
    min_value: float | None
    max_value: float | None
    mean: float | None
    std_dev: float | None
    skewness: float | None


class OrganReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.ORGAN] = ReferenceKind.ORGAN
    name: str = Field(max_length=100, min_length=1)
    description: str | None


class PatientLabSampleTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.PATIENT_LAB_SAMPLE_TYPE] = (
        ReferenceKind.PATIENT_LAB_SAMPLE_TYPE
    )
    name: str = Field(max_length=255, min_length=1)
    description: str | None


class PdfTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.PDF_TYPE] = ReferenceKind.PDF_TYPE
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "patient_info_line": ReferenceKind.REPORT_READER_FLAG,
        "endoscope_info_line": ReferenceKind.REPORT_READER_FLAG,
        "examiner_info_line": ReferenceKind.REPORT_READER_FLAG,
        "cut_off_above_lines": ReferenceKind.REPORT_READER_FLAG,
        "cut_off_below_lines": ReferenceKind.REPORT_READER_FLAG,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(
        ["cut_off_above_lines", "cut_off_below_lines"]
    )
    name: str = Field(max_length=255, min_length=1)
    patient_info_line: CatalogIdentity
    endoscope_info_line: CatalogIdentity
    examiner_info_line: CatalogIdentity
    cut_off_above_lines: list[CatalogIdentity]
    cut_off_below_lines: list[CatalogIdentity]


class ReportReaderFlagReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.REPORT_READER_FLAG] = (
        ReferenceKind.REPORT_READER_FLAG
    )
    name: str = Field(max_length=255, min_length=1)
    value: str = Field(max_length=255)


class RiskReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.RISK] = ReferenceKind.RISK
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "risk_type": ReferenceKind.RISK_TYPE
    }
    name: str = Field(max_length=100, min_length=1)
    name_de: str | None = Field(max_length=100)
    name_en: str | None = Field(max_length=100)
    description: str | None
    risk_value: float | None
    risk_type: CatalogIdentity | None


class RiskTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.RISK_TYPE] = ReferenceKind.RISK_TYPE
    name: str = Field(max_length=100, min_length=1)
    description: str | None


class SingleCategoricalValueDistributionReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.SINGLE_CATEGORICAL_VALUE_DISTRIBUTION] = (
        ReferenceKind.SINGLE_CATEGORICAL_VALUE_DISTRIBUTION
    )
    name: str = Field(max_length=100, min_length=1)
    categories: dict[str, float]


class TagReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.TAG] = ReferenceKind.TAG
    name: str = Field(max_length=100, min_length=1)


class UnitReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.UNIT] = ReferenceKind.UNIT
    name: str = Field(max_length=100, min_length=1)
    description: str | None
    abbreviation: str | None = Field(max_length=25)


class VideoSegmentationLabelReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.VIDEO_SEGMENTATION_LABEL] = (
        ReferenceKind.VIDEO_SEGMENTATION_LABEL
    )
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    color: str | None = Field(max_length=255)
    order_priority: int


class VideoSegmentationLabelSetReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.VIDEO_SEGMENTATION_LABEL_SET] = (
        ReferenceKind.VIDEO_SEGMENTATION_LABEL_SET
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "labels": ReferenceKind.VIDEO_SEGMENTATION_LABEL
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(["labels"])
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    labels: list[CatalogIdentity]


class CenterResourceReference(CatalogRecordBase):
    identity_fields: ClassVar[tuple[str, ...]] = ("center", "resource", "year")
    record_type: Literal[ReferenceKind.CENTER_RESOURCE] = ReferenceKind.CENTER_RESOURCE
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "center": ReferenceKind.CENTER,
        "resource": ReferenceKind.RESOURCE,
        "transport_emission_factor": ReferenceKind.EMISSION_FACTOR,
        "use_emission_factor": ReferenceKind.EMISSION_FACTOR,
        "unit": ReferenceKind.UNIT,
    }
    name: str | None = Field(max_length=255, min_length=1)
    center: CatalogIdentity
    quantity: float
    resource: CatalogIdentity
    transport_emission_factor: CatalogIdentity | None
    use_emission_factor: CatalogIdentity | None
    year: int
    unit: CatalogIdentity | None


class CenterWasteReference(CatalogRecordBase):
    identity_fields: ClassVar[tuple[str, ...]] = ("center", "waste", "year")
    record_type: Literal[ReferenceKind.CENTER_WASTE] = ReferenceKind.CENTER_WASTE
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "center": ReferenceKind.CENTER,
        "waste": ReferenceKind.WASTE,
        "unit": ReferenceKind.UNIT,
        "emission_factor": ReferenceKind.EMISSION_FACTOR,
    }
    center: CatalogIdentity
    year: int
    waste: CatalogIdentity
    quantity: float
    unit: CatalogIdentity | None
    emission_factor: CatalogIdentity | None


class EmissionFactorReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.EMISSION_FACTOR] = ReferenceKind.EMISSION_FACTOR
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {"unit": ReferenceKind.UNIT}
    name: str = Field(max_length=255, min_length=1)
    unit: CatalogIdentity | None
    value: float


class MaterialReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.MATERIAL] = ReferenceKind.MATERIAL
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "emission_factor": ReferenceKind.EMISSION_FACTOR
    }
    name: str = Field(max_length=255, min_length=1)
    emission_factor: CatalogIdentity | None


class ProductReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.PRODUCT] = ReferenceKind.PRODUCT
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "transport_route": ReferenceKind.TRANSPORT_ROUTE,
        "product_group": ReferenceKind.PRODUCT_GROUP,
    }
    name: str = Field(max_length=255, min_length=1)
    transport_route: CatalogIdentity | None
    product_group: CatalogIdentity | None


class ProductGroupReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.PRODUCT_GROUP] = ReferenceKind.PRODUCT_GROUP
    name: str = Field(max_length=255, min_length=1)


class ProductMaterialReference(CatalogRecordBase):
    identity_fields: ClassVar[tuple[str, ...]] = (
        "product",
        "component",
        "material",
        "unit",
    )
    record_type: Literal[ReferenceKind.PRODUCT_MATERIAL] = (
        ReferenceKind.PRODUCT_MATERIAL
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "material": ReferenceKind.MATERIAL,
        "product": ReferenceKind.PRODUCT,
        "unit": ReferenceKind.UNIT,
    }
    component: str = Field(max_length=255)
    material: CatalogIdentity
    product: CatalogIdentity
    unit: CatalogIdentity
    quantity: float


class ProductWeightReference(CatalogRecordBase):
    identity_fields: ClassVar[tuple[str, ...]] = ("product",)
    record_type: Literal[ReferenceKind.PRODUCT_WEIGHT] = ReferenceKind.PRODUCT_WEIGHT
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "product": ReferenceKind.PRODUCT,
        "unit": ReferenceKind.UNIT,
    }
    name: str | None = Field(max_length=255, min_length=1)
    product: CatalogIdentity
    measured: float | None
    verified: float | None
    manufacturer: float | None
    unit: CatalogIdentity | None


class ProfessionReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.PROFESSION] = ReferenceKind.PROFESSION
    name: str = Field(max_length=100, min_length=1)
    description: str | None


class QualificationReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.QUALIFICATION] = ReferenceKind.QUALIFICATION
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "qualification_types": ReferenceKind.QUALIFICATION_TYPE
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(["qualification_types"])
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    is_active: bool
    qualification_types: list[CatalogIdentity]


class QualificationTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.QUALIFICATION_TYPE] = (
        ReferenceKind.QUALIFICATION_TYPE
    )
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    is_active: bool


class ReferenceProductReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.REFERENCE_PRODUCT] = (
        ReferenceKind.REFERENCE_PRODUCT
    )
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "product": ReferenceKind.PRODUCT,
        "product_group": ReferenceKind.PRODUCT_GROUP,
        "emission_factor_total": ReferenceKind.EMISSION_FACTOR,
        "emission_factor_package": ReferenceKind.EMISSION_FACTOR,
        "emission_factor_product": ReferenceKind.EMISSION_FACTOR,
    }
    name: str = Field(max_length=255, min_length=1)
    product: CatalogIdentity
    product_group: CatalogIdentity
    emission_factor_total: CatalogIdentity | None
    emission_factor_package: CatalogIdentity | None
    emission_factor_product: CatalogIdentity | None


class ResourceReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.RESOURCE] = ReferenceKind.RESOURCE
    name: str = Field(max_length=255, min_length=1)


class ShiftReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.SHIFT] = ReferenceKind.SHIFT
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "shift_types": ReferenceKind.SHIFT_TYPE,
        "required_qualifications": ReferenceKind.QUALIFICATION,
    }
    many_relations: ClassVar[frozenset[str]] = frozenset(
        ["shift_types", "required_qualifications"]
    )
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    is_active: bool
    shift_types: list[CatalogIdentity]
    required_qualifications: list[CatalogIdentity]


class ShiftTypeReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.SHIFT_TYPE] = ReferenceKind.SHIFT_TYPE
    name: str = Field(max_length=255, min_length=1)
    description: str | None
    is_active: bool


class TransportRouteReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.TRANSPORT_ROUTE] = ReferenceKind.TRANSPORT_ROUTE
    relation_targets: ClassVar[dict[str, ReferenceKind]] = {
        "emission_factor": ReferenceKind.EMISSION_FACTOR,
        "unit": ReferenceKind.UNIT,
    }
    distance: float
    name: str = Field(max_length=255, min_length=1)
    emission_factor: CatalogIdentity | None
    unit: CatalogIdentity | None


class WasteReference(CatalogRecordBase):
    record_type: Literal[ReferenceKind.WASTE] = ReferenceKind.WASTE
    name: str = Field(max_length=255, min_length=1)


type ReferenceRecord = Annotated[
    AiModelReference
    | CenterReference
    | ContraindicationReference
    | DateValueDistributionReference
    | DiseaseReference
    | DiseaseClassificationReference
    | DiseaseClassificationChoiceReference
    | EndoscopeReference
    | EndoscopeTypeReference
    | EndoscopyProcessorReference
    | EventReference
    | ExaminationReference
    | ExaminationIndicationReference
    | ExaminationIndicationClassificationReference
    | ExaminationIndicationClassificationChoiceReference
    | ExaminationTimeReference
    | ExaminationTimeTypeReference
    | ExaminationTypeReference
    | FindingReference
    | FindingClassificationReference
    | FindingClassificationChoiceReference
    | FindingClassificationTypeReference
    | FindingInterventionReference
    | FindingInterventionTypeReference
    | FindingTypeReference
    | GenderReference
    | InformationSourceReference
    | InformationSourceTypeReference
    | LabValueReference
    | LabelReference
    | LabelSetReference
    | LabelTypeReference
    | MedicationReference
    | MedicationIndicationReference
    | MedicationIndicationTypeReference
    | MedicationIntakeTimeReference
    | MedicationScheduleReference
    | ModelTypeReference
    | MultipleCategoricalValueDistributionReference
    | NumericValueDistributionReference
    | OrganReference
    | PatientLabSampleTypeReference
    | PdfTypeReference
    | ReportReaderFlagReference
    | RiskReference
    | RiskTypeReference
    | SingleCategoricalValueDistributionReference
    | TagReference
    | UnitReference
    | VideoSegmentationLabelReference
    | VideoSegmentationLabelSetReference
    | CenterResourceReference
    | CenterWasteReference
    | EmissionFactorReference
    | MaterialReference
    | ProductReference
    | ProductGroupReference
    | ProductMaterialReference
    | ProductWeightReference
    | ProfessionReference
    | QualificationReference
    | QualificationTypeReference
    | ReferenceProductReference
    | ResourceReference
    | ShiftReference
    | ShiftTypeReference
    | TransportRouteReference
    | WasteReference,
    Field(discriminator="record_type"),
]


class ReferenceCatalogPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal["1.0"] = "1.0"
    records: list[ReferenceRecord] = Field(min_length=1, max_length=10000)

    @model_validator(mode="after")
    def unique_identities(self) -> Self:
        keys = [record.key for record in self.records]
        if len(keys) != len(set(keys)):
            raise ValueError("Reference catalog contains duplicate identities")
        self.records.sort(
            key=lambda record: (
                record.kind.value,
                record.identity.name,
                record.identity.version or 0,
            )
        )
        return self


CATALOG_RECORD_TYPES: dict[ReferenceKind, type[CatalogRecordBase]] = {
    ReferenceKind.AI_MODEL: AiModelReference,
    ReferenceKind.CENTER: CenterReference,
    ReferenceKind.CONTRAINDICATION: ContraindicationReference,
    ReferenceKind.DATE_VALUE_DISTRIBUTION: DateValueDistributionReference,
    ReferenceKind.DISEASE: DiseaseReference,
    ReferenceKind.DISEASE_CLASSIFICATION: DiseaseClassificationReference,
    ReferenceKind.DISEASE_CLASSIFICATION_CHOICE: DiseaseClassificationChoiceReference,
    ReferenceKind.ENDOSCOPE: EndoscopeReference,
    ReferenceKind.ENDOSCOPE_TYPE: EndoscopeTypeReference,
    ReferenceKind.ENDOSCOPY_PROCESSOR: EndoscopyProcessorReference,
    ReferenceKind.EVENT: EventReference,
    ReferenceKind.EXAMINATION: ExaminationReference,
    ReferenceKind.EXAMINATION_INDICATION: ExaminationIndicationReference,
    ReferenceKind.EXAMINATION_INDICATION_CLASSIFICATION: ExaminationIndicationClassificationReference,
    ReferenceKind.EXAMINATION_INDICATION_CLASSIFICATION_CHOICE: ExaminationIndicationClassificationChoiceReference,
    ReferenceKind.EXAMINATION_TIME: ExaminationTimeReference,
    ReferenceKind.EXAMINATION_TIME_TYPE: ExaminationTimeTypeReference,
    ReferenceKind.EXAMINATION_TYPE: ExaminationTypeReference,
    ReferenceKind.FINDING: FindingReference,
    ReferenceKind.FINDING_CLASSIFICATION: FindingClassificationReference,
    ReferenceKind.FINDING_CLASSIFICATION_CHOICE: FindingClassificationChoiceReference,
    ReferenceKind.FINDING_CLASSIFICATION_TYPE: FindingClassificationTypeReference,
    ReferenceKind.FINDING_INTERVENTION: FindingInterventionReference,
    ReferenceKind.FINDING_INTERVENTION_TYPE: FindingInterventionTypeReference,
    ReferenceKind.FINDING_TYPE: FindingTypeReference,
    ReferenceKind.GENDER: GenderReference,
    ReferenceKind.INFORMATION_SOURCE: InformationSourceReference,
    ReferenceKind.INFORMATION_SOURCE_TYPE: InformationSourceTypeReference,
    ReferenceKind.LAB_VALUE: LabValueReference,
    ReferenceKind.LABEL: LabelReference,
    ReferenceKind.LABEL_SET: LabelSetReference,
    ReferenceKind.LABEL_TYPE: LabelTypeReference,
    ReferenceKind.MEDICATION: MedicationReference,
    ReferenceKind.MEDICATION_INDICATION: MedicationIndicationReference,
    ReferenceKind.MEDICATION_INDICATION_TYPE: MedicationIndicationTypeReference,
    ReferenceKind.MEDICATION_INTAKE_TIME: MedicationIntakeTimeReference,
    ReferenceKind.MEDICATION_SCHEDULE: MedicationScheduleReference,
    ReferenceKind.MODEL_TYPE: ModelTypeReference,
    ReferenceKind.MULTIPLE_CATEGORICAL_VALUE_DISTRIBUTION: MultipleCategoricalValueDistributionReference,
    ReferenceKind.NUMERIC_VALUE_DISTRIBUTION: NumericValueDistributionReference,
    ReferenceKind.ORGAN: OrganReference,
    ReferenceKind.PATIENT_LAB_SAMPLE_TYPE: PatientLabSampleTypeReference,
    ReferenceKind.PDF_TYPE: PdfTypeReference,
    ReferenceKind.REPORT_READER_FLAG: ReportReaderFlagReference,
    ReferenceKind.RISK: RiskReference,
    ReferenceKind.RISK_TYPE: RiskTypeReference,
    ReferenceKind.SINGLE_CATEGORICAL_VALUE_DISTRIBUTION: SingleCategoricalValueDistributionReference,
    ReferenceKind.TAG: TagReference,
    ReferenceKind.UNIT: UnitReference,
    ReferenceKind.VIDEO_SEGMENTATION_LABEL: VideoSegmentationLabelReference,
    ReferenceKind.VIDEO_SEGMENTATION_LABEL_SET: VideoSegmentationLabelSetReference,
    ReferenceKind.CENTER_RESOURCE: CenterResourceReference,
    ReferenceKind.CENTER_WASTE: CenterWasteReference,
    ReferenceKind.EMISSION_FACTOR: EmissionFactorReference,
    ReferenceKind.MATERIAL: MaterialReference,
    ReferenceKind.PRODUCT: ProductReference,
    ReferenceKind.PRODUCT_GROUP: ProductGroupReference,
    ReferenceKind.PRODUCT_MATERIAL: ProductMaterialReference,
    ReferenceKind.PRODUCT_WEIGHT: ProductWeightReference,
    ReferenceKind.PROFESSION: ProfessionReference,
    ReferenceKind.QUALIFICATION: QualificationReference,
    ReferenceKind.QUALIFICATION_TYPE: QualificationTypeReference,
    ReferenceKind.REFERENCE_PRODUCT: ReferenceProductReference,
    ReferenceKind.RESOURCE: ResourceReference,
    ReferenceKind.SHIFT: ShiftReference,
    ReferenceKind.SHIFT_TYPE: ShiftTypeReference,
    ReferenceKind.TRANSPORT_ROUTE: TransportRouteReference,
    ReferenceKind.WASTE: WasteReference,
}
