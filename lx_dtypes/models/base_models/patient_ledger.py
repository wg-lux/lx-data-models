from typing import Dict

from pydantic import Field

from lx_dtypes.models.base_models.patient import Patient
from lx_dtypes.utils.mixins.base_model import AppBaseModel


class PatientLedger(AppBaseModel):
    patients: Dict[str, "Patient"] = Field(default_factory=dict)

    def add_patient(self, patient: "Patient") -> None:
        """Add a Patient to the ledger.

        Args:
            patient (Patient): The Patient instance to add.
        """
        self.patients[patient.uuid] = patient
