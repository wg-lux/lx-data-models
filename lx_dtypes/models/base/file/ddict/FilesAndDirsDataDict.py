from typing import TypedDict


class FilesAndDirsDataDict(TypedDict):
    file: str | None
    dir: str | None
    files: list[str]
    dirs: list[str]
