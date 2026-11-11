from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import SerializedVideoFileDataDict, VideoFileDataDict
from .Pydantic import SerializedVideoFile, VideoFile


class LVidFileLookupType(TypedDict):
    VideoFile: type[VideoFile]
    VideoFileDataDict: type[VideoFileDataDict]
    SerializedVideoFile: type[SerializedVideoFile]
    SerializedVideoFileDataDict: type[SerializedVideoFileDataDict]


l_vid_file_lookup = LVidFileLookupType(
    VideoFile=VideoFile,
    VideoFileDataDict=VideoFileDataDict,
    SerializedVideoFile=SerializedVideoFile,
    SerializedVideoFileDataDict=SerializedVideoFileDataDict,
)


if TYPE_CHECKING:
    from .Django import VideoFileDjango

    class LVidFileDjangoLookupType(TypedDict):
        VideoFileDjango: type[VideoFileDjango]

    l_vid_file_django_lookup: LVidFileDjangoLookupType
    type l_vid_file_django_models = VideoFileDjango


l_vid_file_models = Union[VideoFile]
l_vid_file_ddicts = Union[VideoFileDataDict, SerializedVideoFileDataDict]


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


def __getattr__(name: str) -> object:
    if name not in {
        "VideoFileDjango",
        "LVidFileDjangoLookupType",
        "l_vid_file_django_lookup",
        "l_vid_file_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import VideoFileDjango

    class LVidFileDjangoLookupType(TypedDict):
        VideoFileDjango: type[VideoFileDjango]

    exports: dict[str, object] = {
        "VideoFileDjango": VideoFileDjango,
        "LVidFileDjangoLookupType": LVidFileDjangoLookupType,
        "l_vid_file_django_lookup": LVidFileDjangoLookupType(
            VideoFileDjango=VideoFileDjango
        ),
        "l_vid_file_django_models": VideoFileDjango,
    }
    globals().update(exports)
    return exports[name]
