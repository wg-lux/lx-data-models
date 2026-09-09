from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .json_types import JsonObject


class LocalizedCatalogItem(BaseModel):
    """Localized semantic identity returned by terminology catalog routes."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    name_de: str = ""
    name_en: str = ""
    description: str | None = None

    @model_validator(mode="after")
    def guarantee_localized_names(self) -> Self:
        return self.model_copy(
            update={
                "name_de": (
                    self.name_de
                    if self.name_de and self.name_de != "unknown"
                    else self.name
                ),
                "name_en": (
                    self.name_en
                    if self.name_en and self.name_en != "unknown"
                    else self.name
                ),
            }
        )


class ExaminationCatalogDTO(LocalizedCatalogItem):
    findings: list[JsonObject] = Field(default_factory=list)
    examination_types: list[LocalizedCatalogItem] = Field(default_factory=list)


class IndicationCatalogDTO(LocalizedCatalogItem):
    indication_types: list[LocalizedCatalogItem] = Field(default_factory=list)
    classifications: list[LocalizedCatalogItem] = Field(default_factory=list)
    interventions: list[LocalizedCatalogItem] = Field(default_factory=list)


__all__ = [
    "ExaminationCatalogDTO",
    "IndicationCatalogDTO",
    "LocalizedCatalogItem",
]
