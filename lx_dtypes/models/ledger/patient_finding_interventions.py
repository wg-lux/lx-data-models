from typing import List, Optional

from pydantic import Field

from lx_dtypes.models.base_models.base_model import (
    LedgerBaseModel,
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.core.intervention_shallow import InterventionShallowDataDict
from lx_dtypes.utils.factories.field_defaults import (
    uuid_factory,
)


class PatientFindingInterventionShallowDataDict(LedgerBaseModelDataDict):
    patient_uuid: str
    patient_examination_uuid: Optional[str]
    patient_finding_uuid: str
    intervention_name: str


class PatientFindingInterventionDataDict(PatientFindingInterventionShallowDataDict):
    intervention: InterventionShallowDataDict


class PatientFindingInterventionShallow(LedgerBaseModel):
    uuid: str = Field(default_factory=uuid_factory)
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    intervention_name: str

    @property
    def ddict_shallow(self) -> type[PatientFindingInterventionShallowDataDict]:
        return PatientFindingInterventionShallowDataDict

    # def to_ddict_shallow(self) -> PatientFindingInterventionShallowDataDict:
    #     data_dict = self.ddict_shallow(**self.model_dump())
    #     return data_dict


class PatientFindingIntervention(PatientFindingInterventionShallow):
    intervention: InterventionShallowDataDict

    @property
    def ddict(self) -> type[PatientFindingInterventionDataDict]:
        return PatientFindingInterventionDataDict

    # def to_ddict(self) -> PatientFindingInterventionDataDict:
    #     data_dict = self.ddict(**self.model_dump())
    #     return data_dict


class PatientFindingInterventionsShallowDataDict(LedgerBaseModelDataDict):
    patient_uuid: str
    patient_examination_uuid: Optional[str]
    patient_finding_uuid: str
    finding_name: str
    intervention_uuids: List[str]


class PatientFindingInterventionsDataDict(PatientFindingInterventionsShallowDataDict):
    interventions: List[PatientFindingInterventionDataDict]


class PatientFindingInterventionsShallow(LedgerBaseModel):
    patient_uuid: str
    patient_examination_uuid: Optional[str] = None
    patient_finding_uuid: str
    finding_name: str
    intervention_uuids: List[str] = Field(default_factory=list)

    @property
    def ddict_shallow(self) -> type[PatientFindingInterventionsShallowDataDict]:
        return PatientFindingInterventionsShallowDataDict

    # def to_ddict_shallow(
    #     self,
    # ) -> PatientFindingInterventionsShallowDataDict:
    #     data_dict = self.ddict_shallow(**self.model_dump())
    #     return data_dict


class PatientFindingInterventions(PatientFindingInterventionsShallow):
    interventions: List[PatientFindingIntervention] = Field(default_factory=list)

    @property
    def ddict(self) -> type[PatientFindingInterventionsDataDict]:
        return PatientFindingInterventionsDataDict

    # def to_ddict(self) -> PatientFindingInterventionsDataDict:
    #     data_dict = self.ddict(**self.model_dump())
    #     return data_dict
