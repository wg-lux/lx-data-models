from pathlib import Path
from typing import TypedDict

from pydantic import field_validator

from lx_dtypes.models.base.file.ddict import FilesAndDirsDataDict
from lx_dtypes.models.base.file.pydantic.FilesAndDirs import FilesAndDirsModel
from lx_dtypes.models.model import DtypesModel


########## DataDict
class PatientFileMixInDataDict(TypedDict):
    patient: str | None  # UUID of the patient associated with the video
    patient_examination: (
        str | None
    )  # UUID of the patient examination associated with the video
    fnd: FilesAndDirsDataDict


class SerializedPatientFileMixInDataDict(TypedDict):
    patient: str | None  # UUID of the patient associated with the video
    patient_examination: (
        str | None
    )  # UUID of the patient examination associated with the video
    file: str


########## Pydantic
class PatientFileMixIn(DtypesModel):
    patient: str | None = None  # UUID of the patient associated with the video
    patient_examination: str | None = (
        None  # UUID of the patient examination associated with the video
    )

    fnd: FilesAndDirsModel

    # Validators
    ## Validator to ensure 'file' in 'fnd' is present
    @field_validator("fnd")
    @classmethod
    def validate_fnd_file_present(cls, value: FilesAndDirsModel) -> FilesAndDirsModel:
        if value.file is None:
            raise ValueError("The 'file' attribute in 'fnd' must be present.")
        return value

    @property
    def file(self) -> Path:
        f = self.fnd.file
        if f is None:
            raise ValueError("File path is None")
        return Path(f)


class SerializedPatientFileMixIn(DtypesModel):
    patient: str | None = None  # UUID of the patient associated with the video
    patient_examination: str | None = None

    file: Path
