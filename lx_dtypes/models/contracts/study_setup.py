"""Versioned definitions only; authorization and persistence belong to the host."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .ai_dataset import AIDataSetCreateContract
from .cohort_definition import CohortDefinitionFields

DefinitionId = Annotated[
    str, Field(min_length=1, max_length=128, pattern=r"^[a-z][a-z0-9_]*$")
]


class StudyDatasetDefinition(AIDataSetCreateContract):
    definition_id: DefinitionId


class StudyCohortDefinition(CohortDefinitionFields):
    definition_id: DefinitionId
    # Empty selection means current authorized examination scope, not no records.
    dataset_refs: list[DefinitionId] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def unique_references(self) -> Self:
        if len(self.dataset_refs) != len(set(self.dataset_refs)):
            raise ValueError("dataset_refs must be unique")
        return self


class StudySetupDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["1.0"]
    definition_id: DefinitionId
    definition_version: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]
    datasets: list[StudyDatasetDefinition] = Field(default_factory=list, max_length=500)
    cohorts: list[StudyCohortDefinition] = Field(default_factory=list, max_length=500)

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        if not self.datasets and not self.cohorts:
            raise ValueError("a setup must define at least one dataset or cohort")
        identifiers = [item.definition_id for item in self.datasets]
        identifiers.extend(item.definition_id for item in self.cohorts)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError(
                "definition_id values must be unique across datasets and cohorts"
            )
        dataset_ids = {item.definition_id for item in self.datasets}
        for cohort in self.cohorts:
            if set(cohort.dataset_refs) - dataset_ids:
                raise ValueError(
                    "cohort dataset_refs must reference datasets in this document"
                )
        return self
