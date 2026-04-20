from typing import TypedDict, Union

from .DataDict import (
    PatientVideoFileDataDict,
    # RawPatientVideoFileDataDict,
)
from .Pydantic import (
    PatientVideoFile,
    # RawPatientVideoFile,
)

# from .Django import ( #TODO

# class LPVideoDjangoLookupType(TypedDict): # TODO

# l_p_video_django_lookup = LPVideoDjangoLookupType( # TODO


class LPVideoLookupType(TypedDict):
    PatientVideoFile: type[PatientVideoFile]
    PatientVideoFileDataDict: type[PatientVideoFileDataDict]
    # RawPatientVideoFile: type[RawPatientVideoFile]
    # RawPatientVideoFileDataDict: type[RawPatientVideoFileDataDict]


l_p_video_lookup = LPVideoLookupType(
    PatientVideoFile=PatientVideoFile,
    PatientVideoFileDataDict=PatientVideoFileDataDict,
    # RawPatientVideoFile=RawPatientVideoFile,
    # RawPatientVideoFileDataDict=RawPatientVideoFileDataDict,
)
l_p_video_models = Union[PatientVideoFile]  # Removed RawPatientVideoFile
l_p_video_ddicts = Union[
    PatientVideoFileDataDict
]  # Removed RawPatientVideoFileDataDict
# l_p_video_django_models = Union[PatientVideoFileDjango, RawPatientVideoFileDjango] # TODO

__all__ = [
    "PatientVideoFile",
    # "RawPatientVideoFile",
    "PatientVideoFileDataDict",
    # "RawPatientVideoFileDataDict",
    "l_p_video_lookup",
    "LPVideoLookupType",
    "l_p_video_models",
    "l_p_video_ddicts",
    # "LPVideoDjangoLookupType",
    # "l_p_video_django_lookup",
    # "l_p_video_django_models", # TODO
]
