# lx_dtypes/models/meta/SensitiveMeta
import math
import re
from collections.abc import Mapping
from datetime import date, datetime, time
from functools import lru_cache
from typing import Any, ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from lx_dtypes.factories.literals import str_unknown_factory
from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.ddict import StateBaseModelDataDict
from lx_dtypes.models.base.app_base_model.ddict.MetaBaseModelDataDict import (
    MetaBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.MetaBaseModel import MetaBaseModel
from lx_dtypes.models.base.app_base_model.pydantic.StateBaseModel import StateBaseModel
from lx_dtypes.names import (
    GENDER_OPTIONS_LITERAL,
    SENSITIVE_META_MODEL_LIST_TYPE_FIELDS,
    SENSITIVE_META_MODEL_NESTED_FIELDS,
    SENSITIVE_META_STATE_MODEL_LIST_TYPE_FIELDS,
    SENSITIVE_META_STATE_MODEL_NESTED_FIELDS,
)


class SensitiveMetaStateDataDict(StateBaseModelDataDict):
    sensitive_meta: str
    dob_verified: bool
    name_verified: bool
    examination_date_verified: bool


class SensitiveMetaState(StateBaseModel[SensitiveMetaStateDataDict]):
    sensitive_meta: str
    dob_verified: bool = False
    name_verified: bool = False
    examination_date_verified: bool = False

    @property
    def ddict_class(self) -> type[SensitiveMetaStateDataDict]:
        return SensitiveMetaStateDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return SENSITIVE_META_STATE_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return SENSITIVE_META_STATE_MODEL_NESTED_FIELDS


class SensitiveMetaDataDict(MetaBaseModelDataDict):
    file_path: str | None
    examination_date: date | None
    examination_time: time | None
    casenumber: str | None
    pseudo_patient: str | None
    pseudo_examination: str | None
    gender: str | None
    pseudo_examiners: str | list[str] | None

    sensitive_meta_state: str | SensitiveMetaStateDataDict | None

    first_name: str
    last_name: str
    dob: date | None

    endoscope_type: str | None
    endoscope_sn: str | None
    examiner_first_name: str | None
    examiner_last_name: str | None
    center: str | None

    text: str | None
    anonymized_text: str | None

    external_id: str | None  # TODO was previously a model with fields like origin


class SensitiveMeta(MetaBaseModel[SensitiveMetaDataDict]):
    model_config = ConfigDict(validate_assignment=True)

    _LEGACY_FIELD_ALIASES: ClassVar[dict[str, str]] = {
        "patient_first_name": "first_name",
        "patient_last_name": "last_name",
        "patient_dob": "dob",
        "patient_gender_name": "gender",
        "birth_date": "dob",
        "doctor_first_name": "examiner_first_name",
        "doctor_last_name": "examiner_last_name",
        "hospital": "center",
    }
    _NULL_STRINGS: ClassVar[set[str]] = {
        "",
        "-",
        "n/a",
        "na",
        "none",
        "null",
        "undefined",
        "unknown",
    }
    _UNKNOWN_DEFAULT_FIELDS: ClassVar[set[str]] = {"first_name", "last_name", "gender"}
    _LIST_DEFAULT_FIELDS: ClassVar[set[str]] = {"tags", "pseudo_examiners"}
    _DATE_PATTERNS: ClassVar[tuple[tuple[re.Pattern[str], str], ...]] = (
        (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),
        (re.compile(r"^\d{2}\.\d{2}\.\d{4}$"), "%d.%m.%Y"),
        (re.compile(r"^\d{2}\.\d{2}\.\d{2}$"), "%d.%m.%y"),
        (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "%d/%m/%Y"),
        (re.compile(r"^\d{2}-\d{2}-\d{4}$"), "%d-%m-%Y"),
        (re.compile(r"^\d{4}/\d{2}/\d{2}$"), "%Y/%m/%d"),
    )

    file_path: str | None = None
    examination_date: date | None = None
    examination_time: time | None = None
    casenumber: str | None = None
    pseudo_patient: str | None = None
    pseudo_examination: str | None = None
    gender: GENDER_OPTIONS_LITERAL = Field(default_factory=str_unknown_factory)
    pseudo_examiners: str | list[str] = Field(default_factory=list_of_str_factory)
    sensitive_meta_state: "SensitiveMetaState | None" = None

    first_name: str = Field(default_factory=str_unknown_factory)
    last_name: str = Field(default_factory=str_unknown_factory)
    dob: date | None = None

    endoscope_type: str | None = None
    endoscope_sn: str | None = None
    examiner_first_name: str | None = None
    examiner_last_name: str | None = None
    center: str | None = None

    text: str | None = None
    anonymized_text: str | None = None

    external_id: str | None = (
        None  # TODO was previously a model with fields like origin
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_input_payload(cls, data: Any) -> Any:
        if not isinstance(data, Mapping):
            return data

        normalized: dict[str, Any] = {}
        for raw_key, raw_value in dict(data).items():
            key = cls._LEGACY_FIELD_ALIASES.get(str(raw_key), str(raw_key))
            if key not in cls.model_fields:
                continue
            if key in normalized and cls._is_nonblank(normalized[key]):
                continue
            normalized[key] = cls._normalize_value(raw_value, key)
        return normalized

    @field_validator("*", mode="before")
    @classmethod
    def normalize_field_value(cls, value: Any, info: Any) -> Any:
        return cls._normalize_value(value, getattr(info, "field_name", None))

    @staticmethod
    def _parse_date_like(value: Any) -> date | None:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if not isinstance(value, str):
            return None
        s = value.strip()
        if not s:
            return None
        return SensitiveMeta._parse_date_like_cached(s)

    @staticmethod
    @lru_cache(maxsize=4096)
    def _parse_date_like_cached(value: str) -> date | None:
        for pattern, date_format in SensitiveMeta._DATE_PATTERNS:
            if not pattern.match(value):
                continue
            if date_format == "%Y-%m-%d":
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    return None
            try:
                return datetime.strptime(value, date_format).date()  # noqa: DTZ007
            except ValueError:
                return None
        return None

    @classmethod
    def _normalize_value(cls, value: Any, field_name: str | None = None) -> Any:
        if value is None:
            return cls._unknown_or_none(field_name)
        if isinstance(value, float) and math.isnan(value):
            return cls._unknown_or_none(field_name)
        if (
            isinstance(value, (list, dict, set, tuple))
            and len(value) == 0
            and field_name not in cls._LIST_DEFAULT_FIELDS
        ):
            return cls._unknown_or_none(field_name)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.casefold() in cls._NULL_STRINGS:
                return cls._unknown_or_none(field_name)
            if field_name in {"dob", "examination_date"}:
                return cls._parse_date_like(stripped) or stripped
            return stripped
        return value

    @classmethod
    def _unknown_or_none(cls, field_name: str | None) -> Any:
        if field_name in cls._UNKNOWN_DEFAULT_FIELDS:
            return str_unknown_factory()
        return None

    @classmethod
    def _is_nonblank(cls, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value.strip().casefold() not in cls._NULL_STRINGS
        if isinstance(value, (list, dict, set, tuple)):
            return len(value) > 0
        return True

    @property
    def state(self) -> "SensitiveMetaState":
        state = self.sensitive_meta_state
        assert state is not None, (
            "sensitive_meta_state should never be None due to validator"
        )
        return state

    # ensure each meta always has a valid state referencing its UUID
    @model_validator(mode="after")
    def ensure_sensitive_meta_state(self) -> "SensitiveMeta":
        state = self.sensitive_meta_state
        meta_uuid = str(self.uuid)

        if state is None:
            state = SensitiveMetaState(sensitive_meta=meta_uuid)
        else:
            assert state.sensitive_meta == meta_uuid, (
                "sensitive_meta_state's sensitive_meta field must reference the UUID of the meta"
            )

        object.__setattr__(self, "sensitive_meta_state", state)
        return self

    @model_validator(mode="after")
    def validate_date_order(self) -> "SensitiveMeta":
        if self.dob and self.examination_date and self.examination_date < self.dob:
            dob, examination_date = self.examination_date, self.dob
            object.__setattr__(self, "dob", dob)
            object.__setattr__(self, "examination_date", examination_date)
        return self

    def __getitem__(self, key: str) -> Any:
        normalized_key = self._LEGACY_FIELD_ALIASES.get(key, key)
        if normalized_key in type(self).model_fields:
            return getattr(self, normalized_key)
        raise KeyError(f"Invalid key '{key}' for SensitiveMeta")

    def __setitem__(self, key: str, value: Any) -> None:
        normalized_key = self._LEGACY_FIELD_ALIASES.get(key, key)
        if normalized_key in type(self).model_fields:
            setattr(self, normalized_key, value)
            return
        raise KeyError(f"Invalid key '{key}' for SensitiveMeta")

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "SensitiveMeta":
        return cls.model_validate(dict(data or {}))

    def safe_update(
        self,
        data: "SensitiveMeta | BaseModel | Mapping[str, Any] | None" = None,
        **kwargs: Any,
    ) -> None:
        payload: dict[str, Any] = {}

        if isinstance(data, BaseModel):
            payload.update(data.model_dump())
        elif isinstance(data, Mapping):
            payload.update(dict(data))
        elif data is not None:
            return

        if kwargs:
            payload.update(kwargs)
        if not payload:
            return

        try:
            validated_updates = SensitiveMeta.model_validate(payload)
        except ValidationError:
            return

        current_payload = self.model_dump()
        fill_updates = {
            field: new_value
            for field, new_value in validated_updates.model_dump().items()
            if field in type(self).model_fields
            and field not in {"uuid", "created_at", "sensitive_meta_state"}
            and self._is_nonblank(new_value)
            and not self._is_nonblank(getattr(self, field))
        }
        if not fill_updates:
            return

        merged_payload = current_payload | fill_updates
        try:
            merged = SensitiveMeta.model_validate(merged_payload)
        except ValidationError:
            return

        for field, value in merged.model_dump().items():
            object.__setattr__(self, field, value)
        self.__pydantic_fields_set__.update(fill_updates.keys())

    @property
    def ddict_class(self) -> type[SensitiveMetaDataDict]:
        return SensitiveMetaDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return SENSITIVE_META_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return SENSITIVE_META_MODEL_NESTED_FIELDS
