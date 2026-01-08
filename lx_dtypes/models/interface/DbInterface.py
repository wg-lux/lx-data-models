from pathlib import Path
from typing import Self

import yaml

from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.Ledger import Ledger


class DbInterface(AppBaseModelUUIDTags):
    knowledge_base: KnowledgeBase
    ledger: Ledger

    @classmethod
    def create_from_yaml(cls, yaml_path: Path) -> Self:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data_dict = yaml.safe_load(f)

        kb = cls.model_validate(data_dict)
        return kb
