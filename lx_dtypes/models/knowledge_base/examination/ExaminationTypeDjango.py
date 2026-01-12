from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.names import EXAMINATION_TYPE_MODEL_LIST_TYPE_FIELDS

from .ExaminationTypeDataDict import (
    ExaminationTypeDataDict,
)


class ExaminationTypeDjango(KnowledgebaseBaseModelDjango[ExaminationTypeDataDict]):
    if TYPE_CHECKING:
        from .ExaminationDjango import (
            ExaminationDjango,
        )

        examinations: models.QuerySet["ExaminationDjango"]

    @property
    def ddict_class(self) -> type[ExaminationTypeDataDict]:
        return ExaminationTypeDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return EXAMINATION_TYPE_MODEL_LIST_TYPE_FIELDS
