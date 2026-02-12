from typing import List, Union

from pydantic import Field

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ExaminationValidatorDataDict import (
    ExaminationValidatorDataDict,
)


class ExaminationValidator(KnowledgebaseBaseModel[ExaminationValidatorDataDict]):
    finding_validators: Union[str, List[str]] = Field(
        default_factory=list_of_str_factory
    )
    examination_validators: Union[str, List[str]] = Field(
        default_factory=list_of_str_factory
    )

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return ["finding_validators", "examination_validators"]

    @property
    def ddict_class(self) -> type[ExaminationValidatorDataDict]:
        return ExaminationValidatorDataDict
