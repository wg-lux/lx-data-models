from __future__ import annotations

from typing import Self

from pydantic import ConfigDict, Field, field_validator, model_validator

from lx_dtypes.models.model import DtypesModel

from .json_types import JsonObject


class LocalizedCatalogItem(DtypesModel):
    """Localized semantic identity returned by terminology catalog routes."""

    model_config = ConfigDict(
        frozen=True, str_strip_whitespace=True, validate_default=True
    )

    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    name_de: str = ""
    name_en: str = ""
    description: str | None = None

    @field_validator("name_de", "name_en", mode="before")
    @classmethod
    def treat_null_localized_name_as_missing(cls, value: object) -> object:
        # Host ORM localized-name columns are nullable; NULL means "not
        # localized" and takes the same fallback as an empty name.
        return "" if value is None else value

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
