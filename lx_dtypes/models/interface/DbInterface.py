from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.interface.main import KnowledgeBase, Ledger


class DbInterface(AppBaseModelUUIDTags):
    knowledge_base: KnowledgeBase
    ledger: Ledger
