from pathlib import Path

from lx_dtypes.models.base_models.path import FilesAndDirsModel


class TestFilesAndDirsModel:
    def test_get_files_with_suffix(self, tmp_path: Path):
        # Setup test files and directories
        file1 = tmp_path / "file1.txt"
        file1.touch()
        file2 = tmp_path / "file2.md"
        file2.touch()
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        file3 = sub_dir / "file3.txt"
        file3.touch()

        model = FilesAndDirsModel(dir=tmp_path)

        # Test for .txt files
        txt_files = model.get_files_with_suffix(".txt")
        assert len(txt_files) == 2
        assert file1 in txt_files
        assert file3 in txt_files

        # Test for .md files
        md_files = model.get_files_with_suffix(".md")
        assert len(md_files) == 1
        assert file2 in md_files

        # Test for non-existing suffix
        png_files = model.get_files_with_suffix(".png")
        assert len(png_files) == 0
