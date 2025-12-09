from typing import List, Optional

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_patient_finding_classification_choice_factory, uuid_factory
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_finding_classification_choice import PatientFindingClassificationChoice


class PatientFindingClassifications(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    choices: List[PatientFindingClassificationChoice] = Field(default_factory=list_of_patient_finding_classification_choice_factory)
