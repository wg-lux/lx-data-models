from pathlib import Path
from typing import Self

from pydantic import Field, field_validator, model_validator

from lx_dtypes.factories.models import default_data_model_factory
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelNamesUUIDTags import (
    AppBaseModelNamesUUIDTags,
)
from lx_dtypes.models.base.file.pydantic.FilesAndDirs import FilesAndDirsModel
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity


class KnowledgeBaseConfig(AppBaseModelNamesUUIDTags):
    name: str = Field(min_length=1)
    depends_on: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)
    data: FilesAndDirsModel = Field(default_factory=default_data_model_factory)
    version: str = Field(min_length=1)
    medical_field: str | None = None
    author: str | None = None

    @field_validator("depends_on", "modules")
    @classmethod
    def validate_module_references(cls, values: list[str]) -> list[str]:
        if any(not value for value in values):
            raise ValueError("knowledge-base module references must not be empty")
        if len(values) != len(set(values)):
            raise ValueError("knowledge-base module references must be unique")
        return values

    @model_validator(mode="after")
    def validate_dependency_graph_node(self) -> Self:
        if self.name in self.depends_on or self.name in self.modules:
            raise ValueError("a knowledge-base module must not reference itself")
        return self

    @property
    def knowledge_base_identity(self) -> KnowledgeBaseIdentity:
        """Return the same canonical identity used by ledger and API contracts."""

        return KnowledgeBaseIdentity(
            knowledge_base_module=self.name,
            knowledge_base_version=self.version,
        )

    def normalize_data_paths(self, config_file: Path | None) -> None:
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
