from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Self

import yaml
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from lx_dtypes.serialization import serialize_path


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
        arbitrary_types_allowed=False,
    )

    @classmethod
    def from_yaml_file(cls, path: Path) -> Self:
        """Load model instance from a YAML file."""
        path = path.expanduser().resolve()
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["source_file"] = path
        instance = cls.model_validate(data)

        return instance

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Override the default model_dump to exclude certain fields and set defaults."""

        kwargs.setdefault("mode", "python")
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", False)
        # kwargs.setdefault( #TODO revisit
        #     "exclude",
        #     {"source_file", "created_at"} | set(kwargs.get("exclude", [])),
        # )
        kwargs.setdefault("exclude_defaults", False)
        kwargs.setdefault("round_trip", True)

        dump = super().model_dump(*args, **kwargs)
        dump.pop("source_file", None)
        dump.pop("created_at", None)

        return dump

    def to_yaml(self, path: Path) -> None:
        """Serialize the model instance to a YAML string."""
        data = self.model_dump()
        path = path.expanduser().resolve()
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                sort_keys=False,
                allow_unicode=True,
                indent=2,
                encoding="utf-8",
            )
