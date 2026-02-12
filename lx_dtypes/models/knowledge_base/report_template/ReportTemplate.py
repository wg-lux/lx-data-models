from typing import List, Union

from pydantic import Field

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateDataDict import (
    ReportTemplateDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.common import (
    ReportTemplateValidators,
)


class ReportTemplate(KnowledgebaseBaseModel[ReportTemplateDataDict]):
    examination: str
    report_sections: Union[str, List[str]] = Field(default_factory=list_of_str_factory)
    validators: ReportTemplateValidators = Field(
        default_factory=ReportTemplateValidators
    )

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return ["report_sections"]

    @property
    def ddict_class(self) -> type[ReportTemplateDataDict]:
        return ReportTemplateDataDict
