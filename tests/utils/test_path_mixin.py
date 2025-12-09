from pathlib import Path

from lx_dtypes.utils.mixins.path import PathMixin


class TestPathMixin:
    def test_path_mixin_handles_str(self, tmp_path: Path):
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("test content")

        test_file_dir_str = tmp_path.as_posix()
        test_file_path_str = str(test_file)

        class TestModel(
            PathMixin,
        ):
            pass

        instance_from_str_paths = TestModel(
            file=test_file_path_str,  # type: ignore
            dir=test_file_dir_str,  # type: ignore
            files=[test_file_path_str],  # type: ignore
            dirs=[test_file_dir_str],  # type: ignore
        )

        assert instance_from_str_paths.file == test_file
        assert instance_from_str_paths.dir == tmp_path
        assert instance_from_str_paths.files == [test_file]
        assert instance_from_str_paths.dirs == [tmp_path]
