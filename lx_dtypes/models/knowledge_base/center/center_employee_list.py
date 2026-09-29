"""Optional employee recognition lists carried by standard knowledge-base packages."""

from typing import TypedDict

from pydantic import Field, field_validator

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.ledger.examiner.DataDict import ExaminerDataDict
from lx_dtypes.models.ledger.examiner.Pydantic import Examiner


class CenterEmployeeListDataDict(KnowledgebaseBaseModelDataDict):
    examiners: list[ExaminerDataDict]


class CenterEmployeeList(KnowledgebaseBaseModel[CenterEmployeeListDataDict]):
    """Employee entries reuse the ledger contract; center is the host center_key."""

    examiners: list[Examiner] = Field(min_length=1)

    @field_validator("examiners")
    @classmethod
    def validate_recognition_names(cls, examiners: list[Examiner]) -> list[Examiner]:
        for examiner in examiners:
            for value in (examiner.center, examiner.first_name, examiner.last_name):
                if not value.strip() or value == "unknown" or len(value) > 255:
                    raise ValueError(
                        "Employee entries require a center key and nonempty names of at most 255 characters"
                    )
        return examiners

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[CenterEmployeeListDataDict]:
        return CenterEmployeeListDataDict


class KbCenterEmployeeListLookupType(TypedDict):
    CenterEmployeeList: type[CenterEmployeeList]
