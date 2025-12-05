from typing import List

from pydantic import Field

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
