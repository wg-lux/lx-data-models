from typing import List, Optional

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import (
    list_of_patient_finding_classification_choice_factory,
    uuid_factory,
)
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_finding_classification_choice import PatientFindingClassificationChoice


class PatientFindingClassifications(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    finding_name: str
    choices: List[PatientFindingClassificationChoice] = Field(
        default_factory=list_of_patient_finding_classification_choice_factory
    )

    def get_choice_by_uuid(
        self, choice_uuid: str
    ) -> PatientFindingClassificationChoice:
        for choice in self.choices:
            if choice.uuid == choice_uuid:
                return choice
        raise ValueError(f"Choice with UUID '{choice_uuid}' not found.")

    def delete_choice(self, choice_uuid: str):
        choice = self.get_choice_by_uuid(choice_uuid)
        self.choices.remove(choice)
