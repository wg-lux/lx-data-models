from typing import List, Optional

from pydantic import model_validator

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.gender.GenderDataDict import GenderDataDict


class Gender(KnowledgebaseBaseModel[GenderDataDict]):
    abbreviation: Optional[str] = None

    @property
    def ddict_class(self) -> type[GenderDataDict]:
        return GenderDataDict

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return []

    @model_validator(mode="after")
    def fallback_abbreviation(self) -> "Gender":
        if not self.abbreviation:
            self.abbreviation = self.name[:1].upper() if self.name else None
        return self
