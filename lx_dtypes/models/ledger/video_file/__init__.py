from typing import TypedDict, Union

from .DataDict import SerializedVideoFileDataDict, VideoFileDataDict
from .Django import VideoFileDjango
from .Pydantic import SerializedVideoFile, VideoFile


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
    "LVidFileDjangoLookupType",
    "LVidFileLookupType",
    "SerializedVideoFile",
    "SerializedVideoFileDataDict",
    "VideoFile",
    "VideoFileDataDict",
    "l_vid_file_ddicts",
    "l_vid_file_django_lookup",
    "l_vid_file_django_models",
    "l_vid_file_lookup",
    "l_vid_file_models",
]
