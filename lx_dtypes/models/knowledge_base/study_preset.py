"""Host reference-data presets carried by the standard knowledge-base loader."""

from typing import Self, TypedDict

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.contracts.study_metadata import (
    StudyMetadata,
    StudyMetadataDataDict,
)
from lx_dtypes.models.ledger.center.DataDict import CenterDataDict
from lx_dtypes.models.ledger.center.Pydantic import Center


class PresetGender(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=255)
    abbreviation: str | None = Field(default=None, max_length=255)
    description: str | None = None


class PresetLabelType(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class PresetLabel(PresetLabelType):
    label_type: str | None = Field(default=None, min_length=1, max_length=255)


class PresetLabelSet(PresetLabelType):
    version: int
    labels: list[str] = Field(default_factory=list)


class PresetGenderDataDict(TypedDict):
    name: str
    abbreviation: str | None
    description: str | None


class PresetLabelTypeDataDict(TypedDict):
    name: str
    description: str | None


class PresetLabelDataDict(PresetLabelTypeDataDict):
    label_type: str | None


class PresetLabelSetDataDict(PresetLabelTypeDataDict):
    version: int
    labels: list[str]


class StudyPresetDataDict(KnowledgebaseBaseModelDataDict):
    study_metadata: StudyMetadataDataDict
    centers: list[CenterDataDict]
    genders: list[PresetGenderDataDict]
    label_types: list[PresetLabelTypeDataDict]
    labels: list[PresetLabelDataDict]
    label_sets: list[PresetLabelSetDataDict]


class StudyPreset(KnowledgebaseBaseModel[StudyPresetDataDict]):
    """Center names are stable host center keys; employees remain separate and optional."""

    centers: list[Center] = Field(default_factory=list)
    study_metadata: StudyMetadata = Field(default_factory=StudyMetadata)
    genders: list[PresetGender] = Field(default_factory=list)
    label_types: list[PresetLabelType] = Field(default_factory=list)
    labels: list[PresetLabel] = Field(default_factory=list)
    label_sets: list[PresetLabelSet] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_names(self) -> Self:
        for center in self.centers:
            if "name" not in center.model_fields_set:
                raise ValueError("Preset centers require an explicit stable name")
            if center.examiners:
                raise ValueError(
                    "Use optional center_employee_list records for employees"
                )
        for records in (
            self.centers,
            self.genders,
            self.label_types,
            self.labels,
        ):
            names = [record.name for record in records]
            if any(not name.strip() or len(name) > 255 for name in names):
                raise ValueError(
                    "Preset records require nonempty names of at most 255 characters"
                )
            if len(names) != len(set(names)):
                raise ValueError(
                    "Preset record names must be unique within each collection"
                )
        label_set_keys = [(record.name, record.version) for record in self.label_sets]
        if len(label_set_keys) != len(set(label_set_keys)):
            raise ValueError("Label set names and versions must be unique")
        return self

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[StudyPresetDataDict]:
        return StudyPresetDataDict


class KbStudyPresetLookupType(TypedDict):
    StudyPreset: type[StudyPreset]
