from typing import List

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.base.app_base_model.pydantic.PersonMixIn import Person
from lx_dtypes.names import (
    CENTER_MODEL_LIST_TYPE_FIELDS,
)

from .DataDict import (
    ExaminerDataDict,
)


class Examiner(LedgerBaseModel[ExaminerDataDict], Person):
    center: str = Field(default_factory=str)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return CENTER_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ExaminerDataDict]:
        return ExaminerDataDict
