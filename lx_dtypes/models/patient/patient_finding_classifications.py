from typing import List, Optional, TypedDict

from pydantic import Field, field_serializer

from lx_dtypes.utils.factories.field_defaults import (
    list_of_patient_finding_classification_choice_factory,
    uuid_factory,
)
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_finding_classification_choice import (
    PatientFindingClassificationChoice,
    PatientFindingClassificationChoiceDataDict,
)


class PatientFindingClassificationsDataDict(TypedDict):
    uuid: str
    patient_uuid: str
    patient_examination_uuid: Optional[str]
    patient_finding_uuid: str
    finding_name: str
    choices: List[PatientFindingClassificationChoiceDataDict]


class PatientFindingClassificationsShallowDataDict(TypedDict):
    uuid: str
    patient_uuid: str
    patient_examination_uuid: Optional[str]
    patient_finding_uuid: str
    finding_name: str
    choice_uuids: List[str]


class PatientFindingClassificationsShallow(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    finding_name: str
    choice_uuids: List[str] = Field(default_factory=list)

    @property
    def ddict_shallow(self) -> type[PatientFindingClassificationsShallowDataDict]:
        return PatientFindingClassificationsShallowDataDict

    def to_ddict_shallow(self) -> PatientFindingClassificationsShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class PatientFindingClassifications(PatientFindingClassificationsShallow):
    choices: List[PatientFindingClassificationChoice] = Field(
        default_factory=list_of_patient_finding_classification_choice_factory
    )

    @property
    def ddict(self) -> type[PatientFindingClassificationsDataDict]:
        return PatientFindingClassificationsDataDict

    @field_serializer("choices")
    def serialize_choices(
        self, choices: List[PatientFindingClassificationChoice]
    ) -> List[PatientFindingClassificationChoiceDataDict]:
        return [choice.to_ddict() for choice in choices]

    def get_choice_by_uuid(
        self, choice_uuid: str
    ) -> PatientFindingClassificationChoice:
        for choice in self.choices:
            if choice.uuid == choice_uuid:
                return choice
        raise ValueError(f"Choice with UUID '{choice_uuid}' not found.")

    def delete_choice(self, choice_uuid: str) -> None:
        choice = self.get_choice_by_uuid(choice_uuid)
        self.choices.remove(choice)

    def to_ddict(self) -> PatientFindingClassificationsDataDict:
        data_dict = self.model_dump()
        return self.ddict(**data_dict)

    def to_ddict_shallow(self) -> PatientFindingClassificationsShallowDataDict:
        choice_uuids = [choice.uuid for choice in self.choices]
        data_dict = PatientFindingClassificationsShallowDataDict(
            uuid=self.uuid,
            patient_uuid=self.patient_uuid,
            patient_examination_uuid=self.patient_examination_uuid,
            patient_finding_uuid=self.patient_finding_uuid,
            finding_name=self.finding_name,
            choice_uuids=choice_uuids,
        )
        return data_dict
