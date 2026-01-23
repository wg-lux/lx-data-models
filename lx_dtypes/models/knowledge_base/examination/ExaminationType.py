from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.examination.ExaminationTypeDataDict import (
    ExaminationTypeDataDict,
)
from lx_dtypes.names import EXAMINATION_TYPE_MODEL_LIST_TYPE_FIELDS


class ExaminationType(KnowledgebaseBaseModel[ExaminationTypeDataDict]):
    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Provide the names of fields that should be treated as list-typed for the ExaminationType model.

        Returns:
            List[str]: Names of attributes that are represented as lists in the model.
        """
        return EXAMINATION_TYPE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ExaminationTypeDataDict]:
        """
        The data-dictionary class associated with this model.

        Returns:
            type[ExaminationTypeDataDict]: The ExaminationTypeDataDict type used to represent this model's data dictionary.
        """
        return ExaminationTypeDataDict
