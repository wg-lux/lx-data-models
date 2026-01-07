from typing import Self

from pydantic import Field, model_validator

from lx_dtypes.factories import str_unknown_factory

from .AppBaseModelUUIDTags import AppBaseModelUUIDTags


class AppBaseModelNamesUUIDTags(AppBaseModelUUIDTags):
    name: str
    name_de: str = Field(default_factory=str_unknown_factory)
    name_en: str = Field(default_factory=str_unknown_factory)
    description: str = Field(default_factory=str_unknown_factory)

    @model_validator(mode="after")
    def fallback_translations(self) -> Self:
        """Autofill missing translations with the primary name."""
        if not self.name_en:
            self.name_en = self.name
        if not self.name_de:
            self.name_de = self.name
        return self
