from typing import List, Optional, TypedDict


class FilesAndDirsDataDict(TypedDict):
    file: Optional[str]
    dir: Optional[str]
    files: List[str]
    dirs: List[str]
