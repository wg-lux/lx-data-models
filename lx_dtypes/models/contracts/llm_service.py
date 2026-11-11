from __future__ import annotations

from typing import Literal

from pydantic import Field

from lx_dtypes.models.model import StrictContractModel


def _empty_response_choices() -> list[LLMChatResponseChoicePayload]:
    return []


class LLMChatMessagePayload(StrictContractModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMChatOllamaOptionsPayload(StrictContractModel):
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    num_ctx: int = Field(8192, ge=1)


class LLMChatOllamaPayload(StrictContractModel):
    model: str
    messages: list[LLMChatMessagePayload]
    stream: bool = False
    options: LLMChatOllamaOptionsPayload
    format: str | None = None


class LLMChatOpenAIPayload(StrictContractModel):
    model: str
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    max_tokens: int | None = None
    top_p: float | None = Field(1.0, ge=0.0, le=1.0)
    response_format: dict[str, str] | None = None
    stream: bool = False
    messages: list[LLMChatMessagePayload]


class LLMChatResponseMessagePayload(StrictContractModel):
    role: str | None = None
    content: str = ""


class LLMChatResponseChoicePayload(StrictContractModel):
    message: LLMChatResponseMessagePayload


class LLMChatResponsePayload(StrictContractModel):
    message: LLMChatResponseMessagePayload | None = None
    choices: list[LLMChatResponseChoicePayload] = Field(
        default_factory=_empty_response_choices
    )


__all__ = [
    "LLMChatMessagePayload",
    "LLMChatOllamaOptionsPayload",
    "LLMChatOllamaPayload",
    "LLMChatOpenAIPayload",
    "LLMChatResponseChoicePayload",
    "LLMChatResponseMessagePayload",
    "LLMChatResponsePayload",
]
