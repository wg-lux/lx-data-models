import datetime
from typing import List, NamedTuple, Optional, Union

from pydantic import AwareDatetime, Field, field_validator

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding
from lx_dtypes.models.ledger.p_finding_classification_choice.Pydantic import (
    PFindingClassificationChoice,
)
from lx_dtypes.models.ledger.p_indication.Pydantic import PIndication
from lx_dtypes.names import (
    P_EXAMINATION_MODEL_LIST_TYPE_FIELDS,
    P_EXAMINATION_MODEL_NESTED_FIELDS,
)

from .DataDict import (
    PExaminationDataDict,
    SerializedPExaminationDataDict,
)

PFindingClassificationChoiceLookupTuple = NamedTuple(
    "PFindingClassificationChoiceLookupTuple",
    [
        ("p_examination_uuid", str),
        ("p_finding_uuid", str),
        ("p_finding_classifications_uuid", str),
        ("p_finding_classification_choice", PFindingClassificationChoice),
    ],
)


class PExamination(LedgerBaseModel[PExaminationDataDict]):
    patient: str
    examiners: Union[str, List[str]] = Field(default_factory=list_of_str_factory)
    date: Optional[AwareDatetime] = None
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
    ) -> Optional[AwareDatetime]:
        if isinstance(v, str):
            try:
                return datetime.datetime.fromisoformat(v)
            except ValueError:
                return None
        if isinstance(v, datetime.datetime):
            return v
        if isinstance(v, datetime.date):
            return datetime.datetime(
                year=v.year, month=v.month, day=v.day, tzinfo=datetime.timezone.utc
            )
        return v

    def get_finding_by_uuid(self, finding_uuid: str) -> PFinding:
        for finding in self.patient_findings:
            if str(finding.uuid) == finding_uuid:
                return finding
        raise KeyError(
            f"Finding with UUID {finding_uuid} not found in this examination."
        )

    @property
    def serialized_ddict_class(self) -> type[SerializedPExaminationDataDict]:
        return SerializedPExaminationDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPExamination"]:
        return SerializedPExamination

    def get_finding_classification_choice_by_uuid(
        self, finding_classification_choice_uuid: str
    ) -> PFindingClassificationChoiceLookupTuple:
        lookup_tuple: Optional[PFindingClassificationChoiceLookupTuple] = None
        for finding in self.patient_findings:
            for classifications_list in finding.patient_finding_classifications:
                for (
                    classification_choice
                ) in classifications_list.patient_finding_classification_choices:
                    if (
                        str(classification_choice.uuid)
                        == finding_classification_choice_uuid
                    ):
                        lookup_tuple = PFindingClassificationChoiceLookupTuple(
                            p_examination_uuid=str(self.uuid),
                            p_finding_uuid=str(finding.uuid),
                            p_finding_classifications_uuid=str(
                                classifications_list.uuid
                            ),
                            p_finding_classification_choice=classification_choice,
                        )
        if lookup_tuple is None:
            raise KeyError(
                f"Finding Classification Choice with UUID {finding_classification_choice_uuid} not found in this examination."
            )
        return lookup_tuple


class SerializedPExamination(LedgerBaseModel[SerializedPExaminationDataDict]):
    patient: str
    examiners: Union[str, List[str]] = Field(default_factory=list_of_str_factory)
    date: Optional[AwareDatetime] = None
    examination: str
    patient_findings: str = ""
    patient_indications: str = ""

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return P_EXAMINATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[SerializedPExaminationDataDict]:
        return SerializedPExaminationDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        return []
