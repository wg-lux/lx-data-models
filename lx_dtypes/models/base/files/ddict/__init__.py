from enum import Enum

from .FilesAndDirsDataDict import FilesAndDirsDataDict

FilesDDictEnum = Enum(
    "FilesDDictEnum",
    {
        "FilesAndDirsDataDict": FilesAndDirsDataDict,
    },
)

__all__ = ["FilesAndDirsDataDict", "FilesDDictEnum"]
