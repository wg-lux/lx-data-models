from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def _empty_response_choices() -> list["LLMChatResponseChoicePayload"]:
    return []


class LLMChatMessagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    role: Literal["system", "user", "assistant"]
    content: str


class LLMChatOllamaOptionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    temperature: float = Field(0.0, ge=0.0, le=2.0)
    num_ctx: int = Field(8192, ge=1)


class LLMChatOllamaPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    model: str
    messages: list[LLMChatMessagePayload]
    stream: bool = False
    options: LLMChatOllamaOptionsPayload
    format: str | None = None


class LLMChatOpenAIPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    model: str
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    max_tokens: int | None = None
    top_p: float | None = Field(1.0, ge=0.0, le=1.0)
    response_format: dict[str, str] | None = None
    stream: bool = False
    messages: list[LLMChatMessagePayload]


class LLMChatResponseMessagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    role: str | None = None
    content: str = ""


class LLMChatResponseChoicePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    message: LLMChatResponseMessagePayload


class LLMChatResponsePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    message: LLMChatResponseMessagePayload | None = None
    choices: list[LLMChatResponseChoicePayload] = Field(
        default_factory=_empty_response_choices
    )


__all__ = [
    "LLMChatMessagePayload",
    "LLMChatOllamaPayload",
    "LLMChatOllamaOptionsPayload",
    "LLMChatOpenAIPayload",
    "LLMChatResponseChoicePayload",
    "LLMChatResponseMessagePayload",
    "LLMChatResponsePayload",
]
