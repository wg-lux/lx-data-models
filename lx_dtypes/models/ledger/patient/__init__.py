from typing import TypedDict, Union

from .DataDict import (
    PatientDataDict,
)
from .Django import (
    PatientDjango,
)
from .Pydantic import (
    Patient,
)


class LPatientDjangoLookupType(TypedDict):
    Patient: type[PatientDjango]


l_patient_django_lookup = LPatientDjangoLookupType(
    Patient=PatientDjango,
)


class LPatientLookupType(TypedDict):
    Patient: type[Patient]
    PatientDataDict: type[PatientDataDict]


l_patient_lookup = LPatientLookupType(
    Patient=Patient,
    PatientDataDict=PatientDataDict,
)

l_patient_models = Union[Patient,]
l_patient_ddicts = Union[PatientDataDict,]
l_patient_django_models = Union[PatientDjango,]

__all__ = [
    "LPatientDjangoLookupType",
    "LPatientLookupType",
    "Patient",
    "PatientDataDict",
    "l_patient_ddicts",
    "l_patient_django_lookup",
    "l_patient_django_models",
    "l_patient_lookup",
    "l_patient_models",
]
