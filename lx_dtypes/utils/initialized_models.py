from lx_dtypes.models.patient.patient_ledger import PatientLedger
from lx_dtypes.models.examiner import (
    Examiner,  # for model rebuild # type: ignore # noqa: F401
)

PatientLedger.model_rebuild()
