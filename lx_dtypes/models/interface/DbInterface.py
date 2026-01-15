from pathlib import Path
from typing import Self

import yaml

from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase, KnowledgeBaseDDict
from lx_dtypes.models.interface.Ledger import Ledger, LedgerDataDict


class DbInterfaceDataDict(
    AppBaseModelUUIDTagsDataDict,
):
    knowledge_base: KnowledgeBaseDDict
    ledger: LedgerDataDict


class DbInterface(AppBaseModelUUIDTags):
    knowledge_base: KnowledgeBase
    ledger: Ledger

    @classmethod
    def create_from_yaml(cls, yaml_path: Path) -> Self:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data_dict = yaml.safe_load(f)

        kb = cls.model_validate(data_dict)
        return kb

    @classmethod
    def create_empty(cls, name: str, version: str) -> Self:
        from lx_dtypes.models.interface.KnowledgeBaseConfig import (
            KnowledgeBaseConfig,
        )

        kb_cfg = KnowledgeBaseConfig(name=name, version=version)
        db_interface = cls(
            knowledge_base=KnowledgeBase.create_from_config(kb_cfg),
            ledger=Ledger(),
        )
        return db_interface
