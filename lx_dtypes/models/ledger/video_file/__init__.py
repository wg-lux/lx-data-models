from typing import TypedDict, Union

from .DataDict import VideoFileDataDict, SerializedVideoFileDataDict
from .Django import VideoFileDjango
from .Pydantic import VideoFile, SerializedVideoFile


class LVidFileLookupType(TypedDict):
    VideoFile: type[VideoFile]
    VideoFileDataDict: type[VideoFileDataDict]
    SerializedVideoFile: type[SerializedVideoFile]
    SerializedVideoFileDataDict: type[SerializedVideoFileDataDict]
    VideoFileDjango: type[VideoFileDjango]


l_vid_file_lookup = LVidFileLookupType(
    VideoFile=VideoFile,
    VideoFileDataDict=VideoFileDataDict,
    SerializedVideoFile=SerializedVideoFile,
    SerializedVideoFileDataDict=SerializedVideoFileDataDict,
    VideoFileDjango=VideoFileDjango,
)


class LVidFileDjangoLookupType(TypedDict):
    VideoFileDjango: type[VideoFileDjango]


l_vid_file_django_lookup = LVidFileDjangoLookupType(
    VideoFileDjango=VideoFileDjango,
)


l_vid_file_models = Union[VideoFile]
l_vid_file_ddicts = Union[VideoFileDataDict, SerializedVideoFileDataDict]
l_vid_file_django_models = Union[VideoFileDjango]


__all__ = [
    "VideoFile",
    "SerializedVideoFile",
    "VideoFileDataDict",
    "SerializedVideoFileDataDict",
    "l_vid_file_lookup",
    "l_vid_file_django_lookup",
    "LVidFileLookupType",
    "l_vid_file_models",
    "l_vid_file_django_models",
    "l_vid_file_ddicts",
    "LVidFileDjangoLookupType",
]
