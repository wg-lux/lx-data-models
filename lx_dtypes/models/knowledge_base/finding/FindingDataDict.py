from typing import NotRequired

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.contracts.json_types import JsonValue


class FindingDataDict(KnowledgebaseBaseModelDataDict):
    text_extraction: NotRequired[list[dict[str, JsonValue]]]
    classifications: list[str]
    interventions: list[str]
    caused_by_interventions: list[str]
    finding_types: list[str]
