from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.base.app_base_model.pydantic.PersonMixIn import Person
from lx_dtypes.names import PATIENT_MODEL_LIST_TYPE_FIELDS, PATIENT_MODEL_NESTED_FIELDS

from .DataDict import (
    PatientDataDict,
)


class Patient(LedgerBaseModel[PatientDataDict], Person):
    center: str = Field(default_factory=str)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return PATIENT_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PatientDataDict]:
        return PatientDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return PATIENT_MODEL_NESTED_FIELDS
