"""Explicit dataset lifecycle commands shared by file, API and UI boundaries."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import ConfigDict, Field, model_validator

from lx_dtypes.models.model import StrictContractModel

from .ai_dataset import AIDataSetCreateContract


class DatasetDetails(StrictContractModel):
    model_config = ConfigDict(str_strip_whitespace=True)
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


class DatasetSplit(StrictContractModel):
    partitions: list[DatasetPartition] = Field(min_length=2, max_length=20)

    @model_validator(mode="after")
    def disjoint_patients(self) -> Self:
        patients = [patient for part in self.partitions for patient in part.patients]
        if len(patients) != len(set(patients)):
            raise ValueError("Every patient must belong to exactly one partition")
        return self


class DatasetDelete(StrictContractModel):
    mode: Literal["memberships_only", "exclusive_imported_records"]
    preview: str = Field(min_length=1, max_length=2000000)
