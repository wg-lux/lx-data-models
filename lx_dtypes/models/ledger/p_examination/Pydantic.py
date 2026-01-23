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
        """
        Identify model fields that should be treated as list types.

        Returns:
            list_type_fields (List[str]): Field names that represent list-typed attributes for this model.
        """
        return P_EXAMINATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[PExaminationDataDict]:
        """
        Return the DataDict class used to represent this model's data dictionary.

        Returns:
            The `PExaminationDataDict` type associated with this model.
        """
        return PExaminationDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        """
        Return the list of model field names that should be treated as nested (serialized separately).

        Returns:
            List[str]: Field names that contain nested/complex structures for this model.
        """
        return P_EXAMINATION_MODEL_NESTED_FIELDS

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(
        cls, v: Optional[Union[str, datetime.date, datetime.datetime]]
    ) -> Optional[AwareDatetime]:
        """
        Normalize a string/date/datetime input into an aware datetime or return None.

        Parameters:
            v (Optional[Union[str, datetime.date, datetime.datetime]]): Input value to normalize. Accepted forms:
                - ISO 8601 datetime string: parsed to a datetime; returns None if parsing fails.
                - datetime: returned with timezone set to UTC if it is naive; returned unchanged if tz-aware.
                - date: converted to a datetime at midnight UTC.
                - Any other value: returned unchanged.

        Returns:
            Optional[AwareDatetime]: The resulting timezone-aware datetime in UTC for parsed/converted inputs, `None` when an ISO string fails to parse, or the original value for unsupported types.
        """
        if isinstance(v, str):
            try:
                return datetime.datetime.fromisoformat(v)
            except ValueError:
                return None
        if isinstance(v, datetime.datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=datetime.timezone.utc)
            return v
        if isinstance(v, datetime.date):
            return datetime.datetime(
                year=v.year, month=v.month, day=v.day, tzinfo=datetime.timezone.utc
            )
        return v

    def get_finding_by_uuid(self, finding_uuid: str) -> PFinding:
        """
        Retrieve a PFinding from this examination by its UUID.

        Parameters:
            finding_uuid (str): UUID of the finding to locate (string form).

        Returns:
            PFinding: The matching finding object.

        Raises:
            KeyError: If no finding with the specified UUID exists in this examination.
        """
        for finding in self.patient_findings:
            if str(finding.uuid) == finding_uuid:
                return finding
        raise KeyError(
            f"Finding with UUID {finding_uuid} not found in this examination."
        )

    @property
    def serialized_ddict_class(self) -> type[SerializedPExaminationDataDict]:
        """
        Return the DataDict class used for the serialized PExamination model.

        Returns:
            type[SerializedPExaminationDataDict]: The DataDict class representing serialized examination data.
        """
        return SerializedPExaminationDataDict

    @classmethod
    def serialized_model_class(cls) -> type["SerializedPExamination"]:
        """
        Provide the SerializedPExamination model class associated with this model.

        Returns:
            The `SerializedPExamination` model class.
        """
        return SerializedPExamination

    def get_finding_classification_choice_by_uuid(
        self, finding_classification_choice_uuid: str
    ) -> PFindingClassificationChoiceLookupTuple:
        """
        Locate a PFindingClassificationChoice within this examination by its UUID.

        Parameters:
            finding_classification_choice_uuid (str): UUID of the finding classification choice to locate.

        Returns:
            PFindingClassificationChoiceLookupTuple: Tuple containing:
                - p_examination_uuid: UUID of this examination as a string.
                - p_finding_uuid: UUID of the parent finding as a string.
                - p_finding_classifications_uuid: UUID of the parent classifications group as a string.
                - p_finding_classification_choice: The matched PFindingClassificationChoice object.

        Raises:
            KeyError: If no matching finding classification choice UUID is found in this examination.
        """
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
        """
        Identify model fields that should be treated as list types.

        Returns:
            list_type_fields (List[str]): Field names that represent list-typed attributes for this model.
        """
        return P_EXAMINATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[SerializedPExaminationDataDict]:
        """
        Data-dictionary class for the serialized form of this examination model.

        Returns:
            type[SerializedPExaminationDataDict]: The SerializedPExaminationDataDict class used for serialized data dictionaries.
        """
        return SerializedPExaminationDataDict

    @classmethod
    def nested_fields(cls) -> List[str]:
        """
        Provide the names of fields that should be treated as nested models during serialization.

        Returns:
            List[str]: An empty list indicating there are no nested fields for this serialized model.
        """
        return []
