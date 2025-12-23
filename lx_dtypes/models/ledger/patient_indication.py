from typing import Dict, Self

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    LedgerBaseModel,
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.core.indication_shallow import IndicationShallowDataDict
from lx_dtypes.utils.factories.field_defaults import uuid_factory


class PatientIndicationShallowDataDict(LedgerBaseModelDataDict):
    patient_uuid: str
    indication_name: str


class PatientIndicationDataDict(PatientIndicationShallowDataDict):
    indication: IndicationShallowDataDict


class PatientIndicationShallow(LedgerBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    indication_name: str

    @property
    def ddict_shallow(self) -> type[PatientIndicationShallowDataDict]:
        return PatientIndicationShallowDataDict

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

    def to_ddict_shallow(self) -> PatientIndicationShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class PatientIndication(PatientIndicationShallow):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    indication_name: str

    @property
    def ddict(self) -> type[PatientIndicationDataDict]:
        return PatientIndicationDataDict

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

    def to_ddict(self) -> PatientIndicationDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict
