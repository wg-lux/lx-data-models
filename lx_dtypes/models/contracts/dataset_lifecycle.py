"""Explicit dataset lifecycle commands shared by file, API and UI boundaries."""

from __future__ import annotations

from typing import Annotated, Literal, Self
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .ai_dataset import AIDataSetCreateContract


class DatasetDetails(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=10000)
    is_active: bool = True


class DatasetCreate(AIDataSetCreateContract):
    dataset_type: Literal["image", "video", "clinical"] = "clinical"


class DatasetCombine(DatasetDetails):
    sources: list[Annotated[int, Field(gt=0)]] = Field(min_length=2, max_length=100)

    @model_validator(mode="after")
    def unique_sources(self) -> Self:
        if len(set(self.sources)) != len(self.sources):
            raise ValueError("Source datasets must be unique")
        return self


class DatasetPartition(DatasetDetails):
    patients: list[Annotated[int, Field(gt=0)]] = Field(min_length=1, max_length=10000)


class DatasetSplit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    partitions: list[DatasetPartition] = Field(min_length=2, max_length=20)

    @model_validator(mode="after")
    def disjoint_patients(self) -> Self:
        patients = [patient for part in self.partitions for patient in part.patients]
        if len(patients) != len(set(patients)):
            raise ValueError("Every patient must belong to exactly one partition")
        return self


class DatasetDelete(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    mode: Literal["memberships_only", "exclusive_imported_records"]
    preview: str = Field(min_length=1, max_length=2000000)
