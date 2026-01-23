from pathlib import Path
from typing import List, Optional

from pydantic import Field

from lx_dtypes.factories.models import default_data_model_factory
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelNamesUUIDTags import (
    AppBaseModelNamesUUIDTags,
)
from lx_dtypes.models.base.file.pydantic.FilesAndDirs import FilesAndDirsModel


class KnowledgeBaseConfig(AppBaseModelNamesUUIDTags):
    depends_on: List[str] = Field(default_factory=list)
    modules: List[str] = Field(default_factory=list)
    data: FilesAndDirsModel = Field(default_factory=default_data_model_factory)
    version: str

    def normalize_data_paths(self, config_file: Optional[Path]) -> None:
        """
        Normalize data paths to absolute paths relative to the knowledge base module.

        Parameters:
            config_file (Optional[Path]): Path to the knowledge base config file used to determine
                the module base directory. If `None`, `self.source_file` is used.

        Raises:
            ValueError: If `config_file` is `None` and `self.source_file` is not set.
        """
        if config_file is None:
            if self.source_file is None:
                raise ValueError("source_file must be set to normalize data paths")
            config_file = self.source_file
        module_base_dir = config_file.parent
        self.data.resolve_paths(module_base_dir)
