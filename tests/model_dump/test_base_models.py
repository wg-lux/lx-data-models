from pathlib import Path
from typing import Dict, Union

import yaml

from lx_dtypes.models.base_models.path import FilesAndDirsModel


class TestDumpBaseModels:
    def test_dump_files_and_dirs_model(self, tmp_path: Path):
        filepath = tmp_path / "file1.txt"
        filepath.touch()
        dirpath = tmp_path / "dir1"
        dirpath.mkdir()
        file2 = tmp_path / "file2.txt"
        file2.touch()
        file3 = tmp_path / "file3.txt"
        file3.touch()
        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        dir3 = tmp_path / "dir3"
        dir3.mkdir()

        # tmp_path_absolute = tmp_path.resolve()

        model = FilesAndDirsModel(
            file=filepath.relative_to(tmp_path),
            dir=dirpath.relative_to(tmp_path),
            files=[file2.relative_to(tmp_path), file3.relative_to(tmp_path)],
            dirs=[dir2.relative_to(tmp_path), dir3.relative_to(tmp_path)],
        )
        model.resolve_paths(tmp_path)

        model_dump = model.model_dump()

        expected_dump: Dict[str, Union[str, list[str]]] = {
            "file": filepath.resolve().as_posix(),
            "dir": dirpath.resolve().as_posix(),
            "files": [file2.resolve().as_posix(), file3.resolve().as_posix()],
            "dirs": [dir2.resolve().as_posix(), dir3.resolve().as_posix()],
        }

        assert model_dump == expected_dump

        # write to yaml file and read back
        yaml_path = tmp_path / "model.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(model_dump, f)

        with open(yaml_path, "r") as f:
            loaded_yaml = yaml.safe_load(f)

        assert loaded_yaml == expected_dump

        # create a new model from the loaded yaml
        new_model = FilesAndDirsModel.model_validate(loaded_yaml)
        new_model.resolve_paths(tmp_path)
        assert new_model.file == filepath.resolve()
