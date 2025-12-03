from pathlib import Path
from typing import Dict, List, Self

from pydantic import Field

from lx_dtypes.models.base_models.path import FilesAndDirsModel
from lx_dtypes.utils.mixins import BaseModelMixin, TaggedBaseModelMixin


def _default_dataloader_dirs_factory():
    return [Path("./data/")]


class DataLoader(BaseModelMixin):
    """Model representing a data loader configuration."""

    # override name field to automatically yield a fixed name
    name: str = "data_loader"
    input_dirs: List[Path] = Field(default_factory=_default_dataloader_dirs_factory)

    def fetch_config_yamls(self) -> List[Path]:
        """Screens the input directories to ensure they exist.
        Then recursively iterates all directories to the end to locate all
        files named 'config.yaml'.

        Returns:
            List[Path]: A list of existing config_files.
        """
        config_files: List[Path] = []
        for input_dir in self.input_dirs:
            if not input_dir.exists() or not input_dir.is_dir():
                continue

            for path in input_dir.rglob("config.yaml"):
                config_files.append(path)

        return config_files


class KnowledgeBaseConfig(BaseModelMixin, TaggedBaseModelMixin):
    """Model representing a knowledge base configuration."""

    depends_on: list[str] = []
    modules: List[str]
    data: FilesAndDirsModel
    version: str
