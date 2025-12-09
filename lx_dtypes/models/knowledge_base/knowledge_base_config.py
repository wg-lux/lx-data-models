from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, field_serializer

from lx_dtypes.models.base_models.path import FilesAndDirsModel
from lx_dtypes.utils.mixins import BaseModelMixin, TaggedMixin


def _default_data_model_factory():
    return FilesAndDirsModel()


def _default_empty_list_factory():
    _list: List[str] = []
    return _list


class KnowledgeBaseConfig(BaseModelMixin, TaggedMixin):
    """Model representing a knowledge base configuration."""

    depends_on: list[str] = Field(default_factory=_default_empty_list_factory)
    modules: List[str] = Field(default_factory=_default_empty_list_factory)
    data: FilesAndDirsModel = Field(default_factory=_default_data_model_factory)
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

    @field_serializer("data")
    def serialize_data(self, data: FilesAndDirsModel) -> Dict[str, Any]:
        r = data.model_dump()
        return r
