from typing import Dict, Self

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import uuid_factory
from lx_dtypes.utils.mixins.base_model import AppBaseModel


class PatientIndication(AppBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    indication_name: str

    @classmethod
    def create(
        cls,
        patient_uuid: str,
        indication_name: str,
    ) -> Self:
        """Factory method to create a PatientIndication instance."""
        model_dict: Dict[str, str] = {
            "patient_uuid": patient_uuid,
            "indication_name": indication_name,
        }
        instance = cls.model_validate(model_dict)
        return instance
