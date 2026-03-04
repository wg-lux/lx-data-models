from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.common import (
    FindingsValidatorOperatorLiteral,
    FindingsValidatorQueryDataDict,
)


class FindingsValidatorDataDict(KnowledgebaseBaseModelDataDict):
    query: FindingsValidatorQueryDataDict
    finding: str
    operator: FindingsValidatorOperatorLiteral
