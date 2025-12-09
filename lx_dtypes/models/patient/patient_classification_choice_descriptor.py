from typing import Optional, Union

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import uuid_factory
from lx_dtypes.utils.mixins.base_model import AppBaseModel


class PatientFindingClassificationChoiceDescriptor(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    patient_finding_classifications_uuid: str
    patient_finding_classification_choice_uuid: str
    descriptor_name: str
    descriptor_value: Union[str, int, float, bool, None] = None
