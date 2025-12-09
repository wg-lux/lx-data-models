from pytest import fixture

from lx_dtypes.models.knowledge_base import KnowledgeBase
from lx_dtypes.models.patient.patient import Patient
from lx_dtypes.models.patient.patient_ledger import PatientLedger
from lx_dtypes.models.patient_interface import PatientInterface


@fixture(scope="function")
def sample_patient_interface(sample_patient_ledger: PatientLedger, lx_knowledge_base: KnowledgeBase) -> PatientInterface:
    patient_interface = PatientInterface(
        knowledge_base=lx_knowledge_base,
        patient_ledger=sample_patient_ledger,
    )
    return patient_interface


@fixture(scope="session")
def sample_patient_ledger_patient_uuid(sample_patient: Patient) -> str:
    return sample_patient.uuid