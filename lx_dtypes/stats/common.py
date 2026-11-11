from pathlib import Path

from pydantic import ConfigDict

from lx_dtypes.models.model import DtypesModel
from lx_dtypes.serialization import serialize_path


class DatasetBaseModel(DtypesModel):
    """Base model for datasets with common configurations."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
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
    )
