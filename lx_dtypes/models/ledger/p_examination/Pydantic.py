import datetime
from typing import List, Optional, Union

from pydantic import Field, field_validator

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding
from lx_dtypes.models.ledger.p_indication.Pydantic import PIndication
from lx_dtypes.names import (
    P_EXAMINATION_MODEL_LIST_TYPE_FIELDS,
    P_EXAMINATION_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PExaminationDataDict,
)


class PExamination(LedgerBaseModel[PExaminationDataDict]):
    examiners: Union[str, List[str]] = Field(default_factory=list_of_str_factory)
    date: Optional[datetime.date] = None
    examination: str
    patient_findings: List[PFinding] = Field(default_factory=list)
    patient_indications: List[PIndication] = Field(default_factory=list)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_EXAMINATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PExaminationDataDict]:
        return PExaminationDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return P_EXAMINATION_MODEL_NESTED_FIELDS

    @field_validator("date", mode="before")
    def validate_date(
        cls, v: Optional[Union[str, datetime.date, datetime.datetime]]
    ) -> Optional[datetime.date]:
        if isinstance(v, str):
            try:
                return datetime.date.fromisoformat(v)
            except ValueError:
                return None
        if isinstance(v, datetime.datetime):
            return v.date()
        return v
