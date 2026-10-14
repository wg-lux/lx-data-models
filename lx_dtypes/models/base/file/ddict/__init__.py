from typing import TypedDict

from .FilesAndDirsDataDict import FilesAndDirsDataDict


class FileModelsDDictsLookupType(TypedDict):
    FilesAndDirsDataDict: type[FilesAndDirsDataDict]


file_models_ddicts_lookup = FileModelsDDictsLookupType(
    FilesAndDirsDataDict=FilesAndDirsDataDict,
)

__all__ = [
    "FileModelsDDictsLookupType",
    "FilesAndDirsDataDict",
    "file_models_ddicts_lookup",
]
