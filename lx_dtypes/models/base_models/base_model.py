from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, NotRequired, Optional, Self, TypedDict

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from lx_dtypes.utils.factories.field_defaults import (
    list_of_str_factory,
    str_unknown_factory,
    uuid_factory,
)
from lx_dtypes.utils.json_encoders import serialize_path


def _empty_path_list() -> List[Path]:
    return []


class DatasetBaseModel(BaseModel):
    """Base model for datasets with common configurations."""

    model_config = ConfigDict(
        # 1. Strips leading/trailing whitespace automatically ("  val  " -> "val")
        str_strip_whitespace=True,
        # 2. Rejects extra fields not defined in the model (Security/Strictness)
        extra="forbid",
        # 3. Validates default values (ensures your defaults aren't broken)
        validate_default=True,
        # 4. Allows population by alias (e.g. accepting "camelCase" input)
        populate_by_name=True,
        ser_json_timedelta="iso8601",
        ser_json_temporal="iso8601",
        val_temporal_unit="seconds",
        ser_json_bytes="utf8",
        val_json_bytes="utf8",
        ser_json_inf_nan="strings",
        regex_engine="rust-regex",
        validate_by_name=False,
        serialize_by_alias=False,
        json_encoders={Path: serialize_path},
        # from_attributes=True,
    )


class AppBaseModelDataDict(TypedDict):
    # source_file: Optional[str]
    # created_at: str
    pass


class AppBaseModel(BaseModel):
    source_file: Path | None = None
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    model_config = ConfigDict(
        # 1. Strips leading/trailing whitespace automatically ("  val  " -> "val")
        str_strip_whitespace=True,
        # 2. Rejects extra fields not defined in the model (Security/Strictness)
        extra="forbid",
        # 3. Validates default values (ensures your defaults aren't broken)
        validate_default=True,
        # 4. Allows population by alias (e.g. accepting "camelCase" input)
        populate_by_name=True,
        ser_json_timedelta="iso8601",
        ser_json_temporal="iso8601",
        val_temporal_unit="seconds",
        ser_json_bytes="utf8",
        val_json_bytes="utf8",
        ser_json_inf_nan="strings",
        regex_engine="rust-regex",
        validate_by_name=False,
        serialize_by_alias=False,
        json_encoders={Path: serialize_path},
        revalidate_instances="always",
        arbitrary_types_allowed=True,
    )

    @classmethod
    def from_yaml_file(cls, path: Path) -> Self:
        """Load model instance from a YAML file."""
        import yaml

        path = path.expanduser().resolve()
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["source_file"] = path
        instance = cls.model_validate(data)

        return instance

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Override the default model_dump to exclude certain fields and set defaults."""

        kwargs.setdefault("mode", "json")
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", False)
        kwargs.setdefault(
            "exclude",
            {"source_file", "created_at"} | set(kwargs.get("exclude", [])),
        )
        kwargs.setdefault("exclude_defaults", False)
        kwargs.setdefault("round_trip", True)

        dump = super().model_dump(*args, **kwargs)
        dump.pop("source_file", None)
        dump.pop("created_at", None)

        return dump


class AppBaseModelUUIDTagsDataDict(AppBaseModelDataDict):
    uuid: str
    tags: List[str]


class AppBaseModelUUIDTags(AppBaseModel):
    """Abstract base model with UUID field."""

    uuid: str = Field(default_factory=uuid_factory)
    tags: List[str] = Field(default_factory=list_of_str_factory)


class AppBaseModelNamesUUIDTagsDataDict(AppBaseModelUUIDTagsDataDict):
    name: str
    name_de: Optional[str]
    name_en: Optional[str]
    description: Optional[str]


class AppBaseModelNamesUUIDTags(AppBaseModelUUIDTags):
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


class KnowledgebaseBaseModelDataDict(AppBaseModelNamesUUIDTagsDataDict):
    kb_module_name: str


class KnowledgebaseBaseModel(AppBaseModelNamesUUIDTags):
    kb_module_name: str = Field(default_factory=str_unknown_factory)


class LedgerBaseModelDataDict(AppBaseModelUUIDTagsDataDict):
    external_ids: NotRequired[Dict[str, str]]


class LedgerBaseModel(AppBaseModelUUIDTags):
    external_ids: Dict[str, str] = Field(default_factory=dict)


class PathMixin(AppBaseModel):
    file: Optional[Path] = None
    dir: Optional[Path] = None
    files: List[Path] = Field(default_factory=_empty_path_list)
    dirs: List[Path] = Field(default_factory=_empty_path_list)

    @staticmethod
    def _ensure_path(value: Path | str) -> Path:
        if isinstance(value, Path):
            return value
        assert isinstance(value, str)
        return Path(value)

    @field_validator("file", "dir", mode="before")
    @classmethod
    def validate_single_path(cls, value: Path | str | None) -> Path | None:
        if not value:
            return None

        return cls._ensure_path(value)

    @field_validator("files", "dirs", mode="before")
    @classmethod
    def validate_paths(cls, value: Iterable[Path | str] | None) -> List[Path]:
        if value is None:
            return []
        if isinstance(value, list):
            return [cls._ensure_path(item) for item in value]
        raise TypeError("Expected a list of paths")
