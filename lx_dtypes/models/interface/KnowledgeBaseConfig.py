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
        """Normalize data paths to absolute paths. Expects the path of the config
        file located in the knowledge base module. If not provided, it will use the
        source_file attribute of the data model.

        """
        if config_file is None:
            if self.source_file is None:
                raise ValueError("source_file must be set to normalize data paths")
            config_file = self.source_file
        module_base_dir = config_file.parent
        self.data.resolve_paths(module_base_dir)
