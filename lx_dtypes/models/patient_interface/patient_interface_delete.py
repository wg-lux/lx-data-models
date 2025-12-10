# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from lx_dtypes.models.patient_interface import PatientInterface


# def delete_examination(patient_interface: "PatientInterface", examination_uuid: str):
#     examination = patient_interface.get_patient_examination_by_uuid(examination_uuid)
#     patient_interface.patient_ledger.delete_patient_examination(examination)
