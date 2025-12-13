from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from lx_dtypes.models.patient_interface.main import PatientInterface
    from lx_dtypes.utils.importer.smartie.schema import SmartieExaminationSchema


class SmartieMapFunction(Protocol):
    def __call__(
        self,
        exam: "SmartieExaminationSchema",
        record_uuid: str,
        patient_interface: "PatientInterface",
    ) -> None: ...
