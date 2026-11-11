from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import (
    PatientDataDict,
)
from .Pydantic import (
    Patient,
)

if TYPE_CHECKING:
    from .Django import PatientDjango

    class LPatientDjangoLookupType(TypedDict):
        Patient: type[PatientDjango]

    l_patient_django_lookup: LPatientDjangoLookupType
    type l_patient_django_models = PatientDjango


class LPatientLookupType(TypedDict):
    Patient: type[Patient]
    PatientDataDict: type[PatientDataDict]


l_patient_lookup = LPatientLookupType(
    Patient=Patient,
    PatientDataDict=PatientDataDict,
)

l_patient_models = Union[Patient,]
l_patient_ddicts = Union[PatientDataDict,]

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


def __getattr__(name: str) -> object:
    if name not in {
        "PatientDjango",
        "LPatientDjangoLookupType",
        "l_patient_django_lookup",
        "l_patient_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PatientDjango

    class LPatientDjangoLookupType(TypedDict):
        Patient: type[PatientDjango]

    exports: dict[str, object] = {
        "PatientDjango": PatientDjango,
        "LPatientDjangoLookupType": LPatientDjangoLookupType,
        "l_patient_django_lookup": LPatientDjangoLookupType(Patient=PatientDjango),
        "l_patient_django_models": PatientDjango,
    }
    globals().update(exports)
    return exports[name]
