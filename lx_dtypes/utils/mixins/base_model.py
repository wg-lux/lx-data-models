from datetime import datetime, timezone
from pathlib import Path
from typing import Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class AppBaseModel(BaseModel):
    source_file: Path | None = None
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_config = ConfigDict(
        # 1. Strips leading/trailing whitespace automatically ("  val  " -> "val")
        str_strip_whitespace=True,
        # 2. Rejects extra fields not defined in the model (Security/Strictness)
        extra="forbid",
        # 3. Validates default values (ensures your defaults aren't broken)
        validate_default=True,
        # 4. Allows population by alias (e.g. accepting "camelCase" input)
        populate_by_name=True,
    )

    @classmethod
    def from_yaml_file(cls, path: Path) -> Self:
        """Load model instance from a YAML file."""
        import yaml

        path = path.expanduser().resolve()
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        instance = cls.model_validate(data)

        instance.source_file = path
        return instance


class BaseModelMixin(AppBaseModel):
    name: str
    name_de: str | None = None
    name_en: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def fallback_translations(self) -> Self:
        """Autofill missing translations with the primary name."""
        if not self.name_en:
            self.name_en = self.name
        if not self.name_de:
            self.name_de = self.name
        return self
