from typing import Dict, List, NotRequired, Optional, Self, TypedDict, Union

from pydantic import Field, field_serializer

from lx_dtypes.models.patient.patient_finding_classification_choice import (
    PatientFindingClassificationChoice,
)
from lx_dtypes.utils.factories.field_defaults import (
    uuid_factory,
)
from lx_dtypes.models.base_models.base_model import AppBaseModel

from .patient_finding_classifications import (
    PatientFindingClassifications,
    PatientFindingClassificationsDataDict,
)


class PatientFindingDataDict(TypedDict):
    uuid: NotRequired[str]
    patient_uuid: str
    patient_examination_uuid: Optional[str]
    finding_name: str
    classifications: NotRequired[PatientFindingClassificationsDataDict]
    classifications_uuid: NotRequired[str]


class PatientFindingShallowDataDict(TypedDict):
    uuid: NotRequired[str]
    patient_uuid: str
    patient_examination_uuid: Optional[str]
    finding_name: str
    classifications_uuid: NotRequired[str]


class PatientFindingShallow(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    finding_name: str
    classifications_uuid: Optional[str] = None

    @property
    def ddict_shallow(self) -> type[PatientFindingShallowDataDict]:
        return PatientFindingShallowDataDict

    def to_ddict_shallow(self) -> PatientFindingShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class PatientFinding(PatientFindingShallow):
    classifications: Optional[PatientFindingClassifications] = None

    @property
    def ddict(self) -> type[PatientFindingDataDict]:
        return PatientFindingDataDict

    @field_serializer("classifications")
    def serialize_classifications(
        self, classifications: Optional[PatientFindingClassifications]
    ) -> PatientFindingClassificationsDataDict:
        if classifications is None:
            classifications = self.get_or_create_classifications()

        return classifications.to_ddict()

    def to_ddict(self) -> PatientFindingDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(self) -> PatientFindingShallowDataDict:
        classifications_uuid = (
            self.classifications.uuid
            if self.classifications
            else self.classifications_uuid
        )
        assert classifications_uuid is not None, "classifications_uuid must be set"
        data_dict = self.ddict_shallow(
            uuid=self.uuid,
            patient_uuid=self.patient_uuid,
            patient_examination_uuid=self.patient_examination_uuid,
            finding_name=self.finding_name,
            classifications_uuid=classifications_uuid,
        )
        return data_dict

    @classmethod
    def create(
        cls,
        patient_uuid: str,
        finding_name: str,
        patient_examination_uuid: Optional[str] = None,
    ) -> Self:
        """Factory method to create a PatientFinding instance.

        Args:
            patient_uuid (str): The UUID of the patient.
            finding_name (str): The name of the finding.
            patient_examination_uuid (Optional[str]): The UUID of the patient examination.

        Returns:
            PatientFinding: The created PatientFinding instance.
        """
        model_dict: Dict[
            str, Optional[Union[str, List[PatientFindingClassifications]]]
        ] = {
            "patient_uuid": patient_uuid,
            "finding_name": finding_name,
            "patient_examination_uuid": patient_examination_uuid,
        }
        instance = cls.model_validate(model_dict)
        _ = instance.get_or_create_classifications()
        return instance

    def get_or_create_classifications(self) -> PatientFindingClassifications:
        if self.classifications is None:
            self.classifications = PatientFindingClassifications(
                patient_uuid=self.patient_uuid,
                patient_examination_uuid=self.patient_examination_uuid,
                patient_finding_uuid=self.uuid,
                finding_name=self.finding_name,
            )
        return self.classifications

    def add_classification_choice(
        self, classification_choice: "PatientFindingClassificationChoice"
    ) -> None:
        classifications = self.get_or_create_classifications()

        assert (
            classification_choice.patient_finding_classifications_uuid
            == classifications.uuid
        )
        assert classification_choice.patient_finding_uuid == self.uuid
        assert classification_choice.patient_uuid == self.patient_uuid

        classifications.choices.append(classification_choice)

    def delete_classification_choice(self, classification_choice_uuid: str) -> None:
        classifications = self.get_or_create_classifications()
        classifications.delete_choice(classification_choice_uuid)
