from typing import TYPE_CHECKING

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.models.base.app_base_model.django.PersonDjango import (
    PersonDjango,
)
from lx_dtypes.names import EXAMINER_MODEL_LIST_TYPE_FIELDS, FieldNames

from .DataDict import (
    ExaminerDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.center.Django import (
        CenterDjango,
    )


class ExaminerDjango(PersonDjango, LedgerBaseModelDjango[ExaminerDataDict]):
    center: models.ForeignKey["CenterDjango", "CenterDjango"] = models.ForeignKey(
        "CenterDjango",
        related_name=FieldNames.EXAMINERS.value,
        on_delete=models.CASCADE,
    )

    @property
    def ddict_class(self) -> type[ExaminerDataDict]:
        """
        Return the data-dictionary class associated with this model.

        Returns:
            type[ExaminerDataDict]: The ExaminerDataDict class used for this model's data dictionaries.
        """
        return ExaminerDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Return the model field names that should be treated as list-typed for the Examiner model.

        Returns:
            list[str]: Field name strings that represent list-typed attributes for ExaminerDjango.
        """
        return EXAMINER_MODEL_LIST_TYPE_FIELDS

    class Meta(PersonDjango.Meta, LedgerBaseModelDjango.Meta):
        abstract = False
