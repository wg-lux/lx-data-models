from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.Ledger import Ledger


class DbInterface(AppBaseModelUUIDTags):
    knowledge_base: KnowledgeBase
    ledger: Ledger
