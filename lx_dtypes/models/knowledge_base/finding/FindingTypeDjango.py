from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import FINDING_TYPE_MODEL_LIST_TYPE_FIELDS

from .FindingTypeDataDict import (
    FindingTypeDataDict,
)


class FindingTypeDjango(KnowledgebaseBaseModelDjango[FindingTypeDataDict]):
    if TYPE_CHECKING:
        from lx_dtypes.models.knowledge_base.finding.FindingDjango import (
            FindingDjango,
        )

        findings: models.QuerySet["FindingDjango"]

    @property
    def ddict_class(self) -> type[FindingTypeDataDict]:
        return FindingTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return FINDING_TYPE_MODEL_LIST_TYPE_FIELDS
