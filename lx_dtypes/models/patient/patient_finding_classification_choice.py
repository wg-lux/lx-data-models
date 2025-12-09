from typing import List, Optional

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_patient_finding_classification_choice_descriptor_factory, uuid_factory
from lx_dtypes.utils.mixins.base_model import AppBaseModel

from .patient_classification_choice_descriptor import PatientFindingClassificationChoiceDescriptor


class PatientFindingClassificationChoice(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    patient_finding_classifications_uuid: str
    classification_name: str
    descriptors: List[PatientFindingClassificationChoiceDescriptor] = Field(default_factory=list_of_patient_finding_classification_choice_descriptor_factory)
