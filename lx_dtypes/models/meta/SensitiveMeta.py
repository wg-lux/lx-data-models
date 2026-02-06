from datetime import date, time
from typing import List, Optional, Union

from pydantic import Field, model_validator

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
    examination_date: Optional[date]
    examination_time: Optional[time]
    casenumber: Optional[str]
    pseudo_patient: Optional[str]
    pseudo_examination: Optional[str]
    gender: Optional[str]
    pseudo_examiners: Optional[Union[str, List[str]]]

    sensitive_meta_state: str

    first_name: str
    last_name: str
    dob: Optional[date]

    endoscope_type: Optional[str]
    endoscope_sn: Optional[str]

    text: Optional[str]
    anonymized_text: Optional[str]

    external_id: Optional[str]  # TODO was previously a model with fields like origin


class SensitiveMeta(MetaBaseModel[SensitiveMetaDataDict]):
    examination_date: Optional[date] = None
    examination_time: Optional[time] = None
    casenumber: Optional[str] = None
    pseudo_patient: Optional[str] = None
    pseudo_examination: Optional[str] = None
    gender: GENDER_OPTIONS_LITERAL = Field(default_factory=str_unknown_factory)
    pseudo_examiners: Union[str, List[str]] = Field(default_factory=list_of_str_factory)
    sensitive_meta_state: "SensitiveMetaState | None" = None

    first_name: str = Field(default_factory=str_unknown_factory)
    last_name: str = Field(default_factory=str_unknown_factory)
    dob: Optional[date] = None

    endoscope_type: Optional[str] = None
    endoscope_sn: Optional[str] = None

    text: Optional[str] = None
    anonymized_text: Optional[str] = None

    external_id: Optional[str] = (
        None  # TODO was previously a model with fields like origin
    )

    @property
    def state(self) -> "SensitiveMetaState":
        state = self.sensitive_meta_state
        assert (
            state is not None
        ), "sensitive_meta_state should never be None due to validator"
        return state

    # ensure each meta always has a valid state referencing its UUID
    @model_validator(mode="after")
    def ensure_sensitive_meta_state(self) -> "SensitiveMeta":
        state = self.sensitive_meta_state
        meta_uuid = str(self.uuid)

        if state is None:
            state = SensitiveMetaState(sensitive_meta=meta_uuid)
        else:
            assert (
                state.sensitive_meta == meta_uuid
            ), "sensitive_meta_state's sensitive_meta field must reference the UUID of the meta"

        self.sensitive_meta_state = state
        return self

    @property
    def ddict_class(self) -> type[SensitiveMetaDataDict]:
        return SensitiveMetaDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return SENSITIVE_META_MODEL_LIST_TYPE_FIELDS

    @classmethod
    def nested_fields(cls) -> list[str]:
        return SENSITIVE_META_MODEL_NESTED_FIELDS
