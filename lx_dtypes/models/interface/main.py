from pathlib import Path
from typing import Dict, List, Optional

from pydantic import Field

from lx_dtypes.factories.models import default_data_model_factory
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelNamesUUIDTags import (
    AppBaseModelNamesUUIDTags,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.base.file.pydantic.FilesAndDirs import FilesAndDirsModel
from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitType import UnitType


def _default_dataloader_dirs_factory() -> List[Path]:
    return [Path("./data/")]


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


class KnowledgeBase(AppBaseModelUUIDTags):
    config: KnowledgeBaseConfig
    unit_type: Dict[str, UnitType] = Field(default_factory=dict)
    unit: Dict[str, Unit] = Field(default_factory=dict)

    # TODO
    # @classmethod
    # def create_from_config(cls, config: "KnowledgeBaseConfig") -> "KnowledgeBase":
    #     source_file = config.source_file
    #     # assert source_file is not None, "Config must have source_file set." # Can be removed?
    #     kb_source_dict: Dict[str, Union["KnowledgeBaseConfig", Path]] = {
    #         "config": config,
    #         # "source_file": source_file, # Can be removed?
    #     }
    #     kb = cls.model_validate(kb_source_dict)
    #     data = config.data
    #     submodule_files = data.get_files_with_suffix(".yaml")
    #     # for sm_file in submodule_files:

    #     # parsed_object_generator = parse_shallow_object(sm_file, kb_module_name=name)
    #     # for parsed_object in parsed_object_generator:


class Ledger(AppBaseModelUUIDTags):
    pass
