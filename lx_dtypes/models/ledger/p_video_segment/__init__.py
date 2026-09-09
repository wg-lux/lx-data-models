from typing import TypedDict, Union

from .DataDict import (
    PVideoSegmentDataDict,
)
from .Pydantic import (
    PVideoSegment,
)

# from .Django import ( #TODO

# class LPVideoDjangoLookupType(TypedDict): # TODO

# l_p_video_django_lookup = LPVideoDjangoLookupType( # TODO

# l_p_video_django_models = Union[PatientVideoFileDjango, RawPatientVideoFileDjango] # TODO


class LPVideoSegmentLookupType(TypedDict):
    PVideoSegment: type[PVideoSegment]
    PVideoSegmentDataDict: type[PVideoSegmentDataDict]


l_p_video_segment_lookup = LPVideoSegmentLookupType(
    PVideoSegment=PVideoSegment,
    PVideoSegmentDataDict=PVideoSegmentDataDict,
)

l_p_video_segment_models = Union[PVideoSegment]
l_p_video_segment_ddicts = Union[PVideoSegmentDataDict]

__all__ = [
    "LPVideoSegmentLookupType",
    "PVideoSegment",
    "PVideoSegmentDataDict",
    "l_p_video_segment_ddicts",
    "l_p_video_segment_lookup",
    "l_p_video_segment_models",
    # "LPVideoSegmentDjangoLookupType",
    # "l_p_video_segment_django_lookup",
    # "l_p_video_segment_django_models", # TODO
]
