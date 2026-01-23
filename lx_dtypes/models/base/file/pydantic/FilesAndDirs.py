from pathlib import Path
from typing import List, Optional

from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import AppBaseModel
from lx_dtypes.utils.paths import get_files_from_dir_recursive

from .PathMixIn import PathMixin


class FilesAndDirsModel(PathMixin, AppBaseModel):
    def resolve_paths(self, base_dir: Path) -> None:
        """
        Normalize and replace the model's path attributes with absolute Path objects resolved relative to base_dir.

        Transforms the attributes `file`, `dir`, each entry of `files`, and each entry of `dirs` (when present) into absolute, resolved Path instances based on the provided base_dir, updating the attributes in place.

        Parameters:
            base_dir (Path): Base directory used to resolve any relative paths.
        """

        if self.file:
            self.file = (base_dir / self.file).expanduser().resolve()
        if self.dir:
            self.dir = (base_dir / self.dir).expanduser().resolve()

        for i, file_path in enumerate(self.files):
            self.files[i] = (base_dir / file_path).expanduser().resolve()

        for i, dir_path in enumerate(self.dirs):
            self.dirs[i] = (base_dir / dir_path).expanduser().resolve()

    def get_files_with_suffix(self, suffix: Optional[str]) -> List[Path]:
        """
        Collects files stored on the model and returns those whose suffix exactly matches the provided value.

        Parameters:
            suffix (Optional[str]): Suffix to match (including the leading dot, e.g. ".py"); only files whose `Path.suffix` equals this value are kept.

        Returns:
            List[Path]: Paths of matching files sorted by filename in alphabetical order.
        """
        all_files = [self.file] if self.file else []
        all_files += [file for file in self.files]

        for directory in self.dirs:
            all_files += get_files_from_dir_recursive(directory)

        if self.dir:
            all_files += get_files_from_dir_recursive(self.dir)

        filtered_files = [file for file in all_files if file.suffix == suffix]

        # sort by filename
        filtered_files.sort(key=lambda x: x.name)

        return filtered_files
