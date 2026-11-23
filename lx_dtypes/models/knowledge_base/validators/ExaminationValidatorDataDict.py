from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ExaminationValidatorDataDict(KnowledgebaseBaseModelDataDict):
    """Serialized :class:`ExaminationValidator` knowledge-base record."""

    finding_validators: list[str]
    examination_validators: list[str]
