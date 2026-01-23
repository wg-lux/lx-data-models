from typing import List, Union

from pydantic import Field

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.examination.ExaminationDataDict import (
    ExaminationDataDict,
)
from lx_dtypes.names import (
    EXAMINATION_MODEL_LIST_TYPE_FIELDS,
)


class Examination(KnowledgebaseBaseModel[ExaminationDataDict]):
    findings: Union[str, List[str]] = Field(default_factory=list_of_str_factory)
    examination_types: Union[str, List[str]] = Field(
        default_factory=list_of_str_factory
    )
    indications: Union[str, List[str]] = Field(default_factory=list_of_str_factory)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Identify the model attributes that should be treated as list-type fields.

        Returns:
            list_type_fields (List[str]): Names of attributes in this model that are considered list-type (i.e., accept a string or list of strings).
        """
        return EXAMINATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ExaminationDataDict]:
        """
        Provide the ExaminationDataDict type associated with this model.

        Returns:
            type[ExaminationDataDict]: The data-dictionary type used to represent Examination instances.
        """
        return ExaminationDataDict
