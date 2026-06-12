from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AiModelSerializerInputPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    name: str = Field(min_length=1)
    description: str | None = None
    model_type: str = Field(min_length=1)


class AiModelSerializerOutputPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    name: str
    description: str | None = None
    model_type: str


def validate_ai_model_serializer_input_payload(
    payload: object,
) -> AiModelSerializerInputPayload:
    return AiModelSerializerInputPayload.model_validate(payload)


def validate_ai_model_serializer_output_payload(
    payload: object,
) -> AiModelSerializerOutputPayload:
    return AiModelSerializerOutputPayload.model_validate(payload)


__all__ = [
    "AiModelSerializerInputPayload",
    "AiModelSerializerOutputPayload",
    "validate_ai_model_serializer_input_payload",
    "validate_ai_model_serializer_output_payload",
]
