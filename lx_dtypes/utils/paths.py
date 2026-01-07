from pathlib import Path
from typing import List


def get_files_from_dir_recursive(directory: Path) -> List[Path]:
    """Recursively get all files from a directory and its subdirectories."""
    if not directory.exists():
        raise ValueError(f"The provided path {directory} does not exist.")

    if not directory.is_dir():
        raise ValueError(f"The provided path {directory} is not a directory.")

    all_files: List[Path] = []
    for path in directory.rglob("*"):
        is_file = path.is_file()
        if is_file:
            all_files.append(path)
    return all_files
