from __future__ import annotations

from pydantic import ConfigDict, Field

from lx_dtypes.models.model import StrictContractModel

from .json_types import JsonObject


class AiModelSerializerInputPayload(StrictContractModel):
    name: str = Field(min_length=1)
    description: str | None = None
    model_type: str = Field(min_length=1)


class AiModelSerializerOutputPayload(StrictContractModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    description: str | None = None
    model_type: str


def validate_ai_model_serializer_input_payload(
    payload: JsonObject,
) -> AiModelSerializerInputPayload:
    return AiModelSerializerInputPayload.model_validate(payload)


def validate_ai_model_serializer_output_payload(
    payload: JsonObject,
) -> AiModelSerializerOutputPayload:
    return AiModelSerializerOutputPayload.model_validate(payload)


__all__ = [
    "AiModelSerializerInputPayload",
    "AiModelSerializerOutputPayload",
    "validate_ai_model_serializer_input_payload",
    "validate_ai_model_serializer_output_payload",
]
