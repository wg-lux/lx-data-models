from __future__ import annotations


from pydantic import BaseModel, ConfigDict, Field
from lx_dtypes.models.contracts.json_types import JsonObject


class SetupConfigDefaultModelsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    primary_classification_model: str = Field(min_length=1)
    primary_labelset: str = Field(min_length=1)


class SetupConfigHuggingFaceFallbackPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    enabled: bool
    repo_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    labelset_name: str = Field(min_length=1)


class SetupConfigAutoGenerationDefaultsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    activation: str = Field(min_length=1)
    mean: str = Field(min_length=1)
    std: str = Field(min_length=1)
    size_x: int
    size_y: int
    axes: str = Field(min_length=1)
    batchsize: int
    num_workers: int


class SetupConfigDataPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    default_models: SetupConfigDefaultModelsPayload
    huggingface_fallback: SetupConfigHuggingFaceFallbackPayload
    weights_search_patterns: list[str]
    weights_search_dirs: list[str]
    auto_generation_defaults: SetupConfigAutoGenerationDefaultsPayload


class SetupConfigModelSpecificDataPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    setup_config: JsonObject = Field(default_factory=dict)


class SetupConfigModelSpecificEntryFieldsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str | None = None
    model: str | None = None


class SetupConfigModelSpecificEntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    fields: SetupConfigModelSpecificEntryFieldsPayload


__all__ = [
    "SetupConfigAutoGenerationDefaultsPayload",
    "SetupConfigDataPayload",
    "SetupConfigDefaultModelsPayload",
    "SetupConfigHuggingFaceFallbackPayload",
    "SetupConfigModelSpecificDataPayload",
    "SetupConfigModelSpecificEntryFieldsPayload",
    "SetupConfigModelSpecificEntryPayload",
]
