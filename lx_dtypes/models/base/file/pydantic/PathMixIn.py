from pathlib import Path
from typing import Iterable, List, Optional

from pydantic import Field, field_validator

from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import AppBaseModel


class PathMixin(AppBaseModel):
    file: Optional[Path] = None
    dir: Optional[Path] = None
    files: List[Path] = Field(default_factory=list)
    dirs: List[Path] = Field(default_factory=list)

    @staticmethod
    def _ensure_path(value: Path | str) -> Path:
        """
        Normalize an input value into a pathlib.Path.

        Parameters:
            value (Path | str): A Path object or a string representing a filesystem path.

        Returns:
            Path: The corresponding pathlib.Path instance.

        Raises:
            AssertionError: If `value` is neither a Path nor a str.
        """
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
