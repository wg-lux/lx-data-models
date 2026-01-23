from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Self

import yaml
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from lx_dtypes.serialization import serialize_path


class AppBaseModel(BaseModel):
    # Exclude from serialization everywhere (including nested models)
    source_file: Path | None = Field(default=None, exclude=True)
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
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
        """
        Create a model instance from a YAML file.

        Reads the YAML content at `path` (tilde expanded and resolved), sets the instance's `source_file` to the resolved path, validates the data against the model, and returns the constructed instance.

        Parameters:
            path (Path): Path to the YAML file to load.

        Returns:
            Self: A validated model instance populated from the YAML content.
        """
        path = path.expanduser().resolve()
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["source_file"] = path
        instance = cls.model_validate(data)

        return instance

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Serialize the model to a dictionary using the file-oriented default dump options.

        This method applies default serialization settings when none are provided: mode='python', by_alias=True, exclude_none=False, exclude_defaults=False, and round_trip=True. Any options passed via kwargs override these defaults.

        Returns:
            dict: Dictionary representation of the model using the effective dump options.
        """

        kwargs.setdefault("mode", "python")
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("exclude_none", False)
        # kwargs.setdefault(  # TODO revisit
        #     "exclude",
        #     {"source_file", "created_at"} | set(kwargs.get("exclude", [])),
        # )
        kwargs.setdefault("exclude_defaults", False)
        kwargs.setdefault("round_trip", True)

        dump = super().model_dump(*args, **kwargs)
        # Defensive: ensure excluded fields are stripped even if config changes elsewhere
        # dump.pop("source_file", None)
        # dump.pop("created_at", None)

        return dump

    def to_yaml(self, path: Path) -> None:
        """
        Write the model instance to a YAML file at the given path.

        The instance is converted to a JSON-compatible mapping and written to the destination
        using UTF-8 encoding, 2-space indentation, preserved key order, and Unicode characters allowed.

        Parameters:
            path (Path): Destination file path; user tilde will be expanded and the path resolved.

        """
        data = self.model_dump(mode="json")
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
