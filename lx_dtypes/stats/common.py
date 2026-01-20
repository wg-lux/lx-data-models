from pathlib import Path

from pydantic import BaseModel, ConfigDict

from lx_dtypes.serialization import serialize_path


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
