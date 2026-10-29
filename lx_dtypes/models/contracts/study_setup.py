"""Versioned definitions only; authorization and persistence belong to the host."""

from __future__ import annotations

import json
from hashlib import sha256
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
    definition_version: Annotated[
        str, Field(max_length=64, pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    ]
    datasets: list[StudyDatasetDefinition] = Field(default_factory=list, max_length=500)
    cohorts: list[StudyCohortDefinition] = Field(default_factory=list, max_length=500)

    @property
    def content_sha256(self) -> str:
        payload = self.model_dump(mode="json")
        # Adding optional analysis or text-extraction authoring must not change
        # the identity of already imported setup documents that contain none.
        for cohort in payload["cohorts"]:
            metadata = cohort["study_metadata"]
            for optional in (
                "analysis_definitions",
                "text_extraction",
                "classification_text_extraction",
            ):
                if not metadata[optional]:
                    metadata.pop(optional)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()

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


class StudySetupImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    yaml: str = Field(max_length=1_048_576)
    mode: Literal["validate", "dry_run", "import"] = "validate"


class StudySetupImportReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    definition: StudySetupDefinition
    datasets: dict[str, Annotated[int, Field(gt=0)]]
    cohorts: dict[str, Annotated[int, Field(gt=0)]]

    @model_validator(mode="after")
    def complete_mapping(self) -> Self:
        if set(self.datasets) != {
            row.definition_id for row in self.definition.datasets
        }:
            raise ValueError("dataset identity mapping is incomplete")
        if set(self.cohorts) != {row.definition_id for row in self.definition.cohorts}:
            raise ValueError("cohort identity mapping is incomplete")
        if len(set(self.datasets.values())) != len(self.datasets) or len(
            set(self.cohorts.values())
        ) != len(self.cohorts):
            raise ValueError("distinct definitions require distinct persisted rows")
        return self


class StudySetupImportResult(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    status: Literal["planned", "created", "unchanged"]
    definition_id: DefinitionId
    definition_version: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    datasets: dict[str, int | None]
    cohorts: dict[str, int | None]
    links: dict[str, list[str]]
