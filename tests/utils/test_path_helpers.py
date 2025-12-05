from pathlib import Path
from typing import Set

from lx_dtypes.utils.paths import get_files_from_dir_recursive


class TestPathHelpers:
    def test_get_files_from_dir_recursive(self, tmp_path: Path):
        # Setup: Create a directory structure with files
        dir_a = tmp_path / "dir_a"
        dir_b = dir_a / "dir_b"
        dir_b.mkdir(parents=True)
        file_1 = dir_a / "file1.txt"
        file_2 = dir_b / "file2.txt"
        file_3 = tmp_path / "file3.txt"
        file_1.write_text("content 1")
        file_2.write_text("content 2")
        file_3.write_text("content 3")

        # Execute
        result = get_files_from_dir_recursive(tmp_path)

        # Verify
        expected_files: Set[Path] = {file_1, file_2, file_3}
        assert set(result) == expected_files

    def test_get_files_from_dir_recursive_empty(self, tmp_path: Path):
        # Setup: Create an empty directory
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()

        # Execute
        result = get_files_from_dir_recursive(empty_dir)

        # Verify
        assert result == []

    def test_get_files_from_dir_recursive_nonexistent(self, tmp_path: Path):
        # Setup: Define a non-existent directory path
        nonexistent_dir = tmp_path / "nonexistent_dir"

        # Execute & Verify
        try:
            get_files_from_dir_recursive(nonexistent_dir)
        except ValueError as e:
            assert str(e) == f"The provided path {nonexistent_dir} does not exist."
