from pathlib import Path
from typing import Iterable, List, Optional

from pydantic import Field, field_validator

from .base_model import AppBaseModel


def _empty_path_list() -> List[Path]:
    return []


class PathMixin(AppBaseModel):
    file: Optional[Path] = None
    dir: Optional[Path] = None
    files: List[Path] = Field(default_factory=_empty_path_list)
    dirs: List[Path] = Field(default_factory=_empty_path_list)

    @staticmethod
    def _ensure_path(value: Path | str) -> Path:
        if isinstance(value, Path):
            return value
        assert isinstance(value, str)
        return Path(value)

    @field_validator("file", "dir", mode="before")
    @classmethod
    def validate_single_path(cls, value: Path | str | None) -> Path | None:
        if not value:
            return None

        return cls._ensure_path(value)

    @field_validator("files", "dirs", mode="before")
    @classmethod
    def validate_paths(cls, value: Iterable[Path | str] | None) -> List[Path]:
        if value is None:
            return []
        if isinstance(value, list):
            return [cls._ensure_path(item) for item in value]
        raise TypeError("Expected a list of paths")
