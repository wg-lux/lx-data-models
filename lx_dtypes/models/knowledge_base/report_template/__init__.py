from typing import TypedDict, Union

from .ExaminationValidator import ExaminationValidator
from .ExaminationValidatorDataDict import ExaminationValidatorDataDict
from .FindingsValidator import FindingsValidator
from .FindingsValidatorDataDict import FindingsValidatorDataDict
from .LookupState import (
    LEGACY_LOOKUP_KEY_MAP,
    LookupInitRequest,
    LookupPartsPatchRequest,
    LookupPartsResponse,
    LookupRecomputeResponse,
    LookupState,
    RequirementSetSummary,
    ValidationError,
    build_lookup_recompute_response,
    normalize_lookup_keys,
    validate_lookup_parts_response,
    validate_lookup_state,
    validate_lookup_updates,
)
from .LookupStateDataDict import (
    LookupDerivedUpdatesDataDict,
    LookupInitRequestDataDict,
    LookupPartsPatchRequestDataDict,
    LookupRecomputeResponseDataDict,
    LookupStateDataDict,
    RequirementSetSummaryDataDict,
)
from .ReportFinding import ReportFinding
from .ReportFindingDataDict import ReportFindingDataDict
from .ReportTemplateGraph import (
    ReportTemplateGraph,
    ReportTemplateGraphEdge,
    ReportTemplateGraphNode,
    ReportTemplateStructureIssue,
    ReportTemplateStructureValidationResult,
    build_report_template_graph,
    validate_report_template_knowledge_base,
    validate_report_template_structure,
)
from .ReportTemplateGraphDataDict import (
    ReportTemplateGraphDataDict,
    ReportTemplateGraphEdgeDataDict,
    ReportTemplateGraphNodeDataDict,
    ReportTemplateStructureIssueDataDict,
    ReportTemplateStructureValidationResultDataDict,
)
from .ReportTemplate import ReportTemplate
from .ReportTemplateDataDict import ReportTemplateDataDict
from .ReportTemplateSection import ReportTemplateSection
from .ReportTemplateSectionDataDict import ReportTemplateSectionDataDict
from .common import (
    DEPRECATED_FINDINGS_VALIDATOR_COMPARATOR_ALIASES,
    DEPRECATED_FINDINGS_VALIDATOR_OPERATOR_ALIASES,
    FINDINGS_VALIDATOR_COMPARATORS,
    FINDINGS_VALIDATOR_OPERATORS,
    DeprecatedReportTemplateValueWarning,
    FindingsValidatorComparator,
    FindingsValidatorCondition,
    FindingsValidatorConditionDataDict,
    FindingsValidatorConditionRule,
    FindingsValidatorConditionRuleDataDict,
    FindingsValidatorOperator,
    FindingsValidatorQuery,
    FindingsValidatorQueryDataDict,
    FindingsValidatorRequiredClassification,
    FindingsValidatorRequiredClassificationDataDict,
)


class KbReportTemplateLookupType(TypedDict):
    ReportTemplate: type[ReportTemplate]
    ReportTemplateDataDict: type[ReportTemplateDataDict]
    ReportTemplateGraph: type[ReportTemplateGraph]
    ReportTemplateGraphDataDict: type[ReportTemplateGraphDataDict]
    ReportTemplateSection: type[ReportTemplateSection]
    ReportTemplateSectionDataDict: type[ReportTemplateSectionDataDict]
    ReportFinding: type[ReportFinding]
    ReportFindingDataDict: type[ReportFindingDataDict]
    FindingsValidator: type[FindingsValidator]
    FindingsValidatorDataDict: type[FindingsValidatorDataDict]
    ExaminationValidator: type[ExaminationValidator]
    ExaminationValidatorDataDict: type[ExaminationValidatorDataDict]
    LookupState: type[LookupState]
    LookupStateDataDict: type[LookupStateDataDict]


kb_report_template_lookup = KbReportTemplateLookupType(
    ReportTemplate=ReportTemplate,
    ReportTemplateDataDict=ReportTemplateDataDict,
    ReportTemplateGraph=ReportTemplateGraph,
    ReportTemplateGraphDataDict=ReportTemplateGraphDataDict,
    ReportTemplateSection=ReportTemplateSection,
    ReportTemplateSectionDataDict=ReportTemplateSectionDataDict,
    ReportFinding=ReportFinding,
    ReportFindingDataDict=ReportFindingDataDict,
    FindingsValidator=FindingsValidator,
    FindingsValidatorDataDict=FindingsValidatorDataDict,
    ExaminationValidator=ExaminationValidator,
    ExaminationValidatorDataDict=ExaminationValidatorDataDict,
    LookupState=LookupState,
    LookupStateDataDict=LookupStateDataDict,
)

kb_report_template_models = Union[
    ReportTemplate,
    ReportTemplateGraph,
    ReportTemplateSection,
    ReportFinding,
    FindingsValidator,
    ExaminationValidator,
    LookupState,
]

kb_report_template_ddicts = Union[
    ReportTemplateDataDict,
    ReportTemplateGraphDataDict,
    ReportTemplateSectionDataDict,
    ReportFindingDataDict,
    FindingsValidatorDataDict,
    ExaminationValidatorDataDict,
    LookupStateDataDict,
]

__all__ = [
    "ReportTemplate",
    "ReportTemplateDataDict",
    "ReportTemplateGraph",
    "ReportTemplateGraphDataDict",
    "ReportTemplateGraphNode",
    "ReportTemplateGraphNodeDataDict",
    "ReportTemplateGraphEdge",
    "ReportTemplateGraphEdgeDataDict",
    "ReportTemplateStructureIssue",
    "ReportTemplateStructureIssueDataDict",
    "ReportTemplateStructureValidationResult",
    "ReportTemplateStructureValidationResultDataDict",
    "ReportTemplateSection",
    "ReportTemplateSectionDataDict",
    "ReportFinding",
    "ReportFindingDataDict",
    "FindingsValidator",
    "FindingsValidatorDataDict",
    "FindingsValidatorOperator",
    "FindingsValidatorComparator",
    "FINDINGS_VALIDATOR_OPERATORS",
    "FINDINGS_VALIDATOR_COMPARATORS",
    "DEPRECATED_FINDINGS_VALIDATOR_OPERATOR_ALIASES",
    "DEPRECATED_FINDINGS_VALIDATOR_COMPARATOR_ALIASES",
    "DeprecatedReportTemplateValueWarning",
    "FindingsValidatorQuery",
    "FindingsValidatorQueryDataDict",
    "FindingsValidatorCondition",
    "FindingsValidatorConditionDataDict",
    "FindingsValidatorConditionRule",
    "FindingsValidatorConditionRuleDataDict",
    "FindingsValidatorRequiredClassification",
    "FindingsValidatorRequiredClassificationDataDict",
    "ExaminationValidator",
    "ExaminationValidatorDataDict",
    "LookupInitRequest",
    "LookupInitRequestDataDict",
    "LookupPartsPatchRequest",
    "LookupPartsPatchRequestDataDict",
    "LookupPartsResponse",
    "LookupRecomputeResponse",
    "LookupRecomputeResponseDataDict",
    "LookupState",
    "LookupStateDataDict",
    "LookupDerivedUpdatesDataDict",
    "RequirementSetSummary",
    "ValidationError",
    "RequirementSetSummaryDataDict",
    "LEGACY_LOOKUP_KEY_MAP",
    "normalize_lookup_keys",
    "validate_lookup_state",
    "validate_lookup_parts_response",
    "validate_lookup_updates",
    "build_lookup_recompute_response",
    "build_report_template_graph",
    "validate_report_template_structure",
    "validate_report_template_knowledge_base",
    "KbReportTemplateLookupType",
    "kb_report_template_lookup",
    "kb_report_template_models",
    "kb_report_template_ddicts",
]
