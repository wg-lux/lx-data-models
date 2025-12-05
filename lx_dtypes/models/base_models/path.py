from pathlib import Path
from typing import List, Optional

from lx_dtypes.utils.mixins import PathMixin
from lx_dtypes.utils.mixins.base_model import AppBaseModel
from lx_dtypes.utils.paths import get_files_from_dir_recursive


class FilesAndDirsModel(PathMixin, AppBaseModel):
    pass

    def resolve_paths(self, base_dir: Path) -> None:
        """Resolve all paths to their absolute forms."""

        if self.file:
            self.file = (base_dir / self.file).expanduser().resolve()
        if self.dir:
            self.dir = (base_dir / self.dir).expanduser().resolve()

        for i, file_path in enumerate(self.files):
            self.files[i] = (base_dir / file_path).expanduser().resolve()

        for i, dir_path in enumerate(self.dirs):
            self.dirs[i] = (base_dir / dir_path).expanduser().resolve()

    def get_files_with_suffix(self, suffix: Optional[str]) -> List[Path]:
        """Get all files with the specified suffix.

        Args:
            suffix (str): The suffix to filter files by.

        Returns:
            list[Path]: A list of files with the specified suffix.
        """
        all_files = [self.file] if self.file else []
        all_files += [file for file in self.files]

        for directory in self.dirs:
            all_files += get_files_from_dir_recursive(directory)

        if self.dir:
            all_files += get_files_from_dir_recursive(self.dir)

        filtered_files = [file for file in all_files if file.suffix == suffix]

        return filtered_files
