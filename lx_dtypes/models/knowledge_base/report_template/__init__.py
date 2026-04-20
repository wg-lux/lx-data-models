from typing import TypedDict, Union

from .ClassificationValidator import (
    CLASSIFICATION_VALIDATOR_OPERATORS,
    CLASSIFICATION_VALIDATOR_PRECEDENCE,
    ClassificationValidator,
    ClassificationValidatorCondition,
    ClassificationValidatorConditionClause,
    ClassificationValidatorOperator,
    ClassificationValidatorPrecedence,
    ClassificationValidatorQuery,
)
from .ClassificationValidatorDataDict import (
    ClassificationValidatorConditionDataDict,
    ClassificationValidatorDataDict,
    ClassificationValidatorHintDataDict,
    ClassificationValidatorQueryDataDict,
)
from .InterventionValidator import (
    INTERVENTION_VALIDATOR_OPERATORS,
    INTERVENTION_VALIDATOR_PRECEDENCE,
    InterventionValidator,
    InterventionValidatorCondition,
    InterventionValidatorConditionClause,
    InterventionValidatorOperator,
    InterventionValidatorPrecedence,
    InterventionValidatorQuery,
)
from .InterventionValidatorDataDict import (
    InterventionValidatorConditionDataDict,
    InterventionValidatorDataDict,
    InterventionValidatorHintDataDict,
    InterventionValidatorQueryDataDict,
)
from .ExaminationValidator import ExaminationValidator
from .ExaminationValidatorDataDict import ExaminationValidatorDataDict
from .FindingsValidator import (
    DEPRECATED_FINDINGS_VALIDATOR_COMPARATOR_ALIASES,
    FINDINGS_VALIDATOR_COMPARATORS,
    FINDINGS_VALIDATOR_OPERATORS,
    DeprecatedReportTemplateValueWarning,
    FindingsValidatorComparator,
    FindingsValidatorCondition,
    FindingsValidatorConditionClause,
    FindingsValidatorOperator,
    FindingsValidatorQuery,
    FindingsValidatorRequiredClassification,
)
from .FindingsValidator import FindingsValidator as FindingsValidatorModel
from .FindingsValidatorDataDict import (
    FindingsValidatorConditionDataDict,
    FindingsValidatorDataDict,
    FindingsValidatorQueryDataDict,
)
from .UnitValidator import (
    UNIT_VALIDATOR_OPERATORS,
    UNIT_VALIDATOR_PRECEDENCE,
    UnitValidator,
    UnitValidatorCondition,
    UnitValidatorConditionClause,
    UnitValidatorOperator,
    UnitValidatorPrecedence,
    UnitValidatorQuery,
)
from .UnitValidatorDataDict import (
    UnitValidatorConditionDataDict,
    UnitValidatorDataDict,
    UnitValidatorHintDataDict,
    UnitValidatorQueryDataDict,
)
from .ValidatorRequirementReference import (
    ValidatorRequirementKind,
    ValidatorRequirementReference,
)
from .ValidatorRequirementReferenceDataDict import (
    ValidatorRequirementKindLiteral,
    ValidatorRequirementReferenceDataDict,
)
from .ReportFinding import (
    ReportFinding,
    ReportTemplateClassificationRequirement,
    ReportTemplateFindingRequirement,
)
from .ReportFindingDataDict import (
    ReportFindingDataDict,
    ReportTemplateClassificationRequirementDataDict,
    ReportTemplateFindingRequirementDataDict,
)
from .ReportTemplate import ReportTemplate, ReportTemplateValidators
from .ReportTemplateDataDict import (
    ReportTemplateDataDict,
    ReportTemplateValidatorsDataDict,
)
from .TemplateReadiness import (
    ReportTemplateIssueScopeLiteral,
    ReportTemplateIssueSeverityLiteral,
    ReportTemplateLifecycleStatusLiteral,
    ReportTemplateReadinessIssue,
    ReportTemplateReadinessIssueDataDict,
    ReportTemplateReadinessLiteral,
    ReportTemplateReadinessSummary,
    ReportTemplateReadinessSummaryDataDict,
)
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
from .ReportTemplateSection import ReportTemplateSection, ReportTemplateSectionField
from .ReportTemplateSectionDataDict import (
    ReportTemplateSectionDataDict,
    ReportTemplateSectionFieldDataDict,
)
from .ValidatorRuntime import (
    ClassificationValidatorExecutionDataDict,
    InterventionValidatorExecutionDataDict,
    ExaminationValidatorDependencyStatusDataDict,
    ExaminationValidatorExecutionDataDict,
    FindingsValidatorExecutionDataDict,
    ReportTemplateRuntimeValidationResultDataDict,
    RuntimeValidationIssueDataDict,
    UnitValidatorExecutionDataDict,
    evaluate_classification_validator_runtime,
    evaluate_findings_validator_runtime,
    evaluate_intervention_validator_runtime,
    evaluate_report_template_validators_runtime,
    evaluate_unit_validator_runtime,
)

FindingsValidator = FindingsValidatorModel


class KbReportTemplateLookupType(TypedDict):
    ReportTemplate: type[ReportTemplate]
    ReportTemplateDataDict: type[ReportTemplateDataDict]
    ReportTemplateGraph: type[ReportTemplateGraph]
    ReportTemplateGraphDataDict: type[ReportTemplateGraphDataDict]
    ReportTemplateSection: type[ReportTemplateSection]
    ReportTemplateSectionDataDict: type[ReportTemplateSectionDataDict]
    ReportFinding: type[ReportFinding]
    ReportFindingDataDict: type[ReportFindingDataDict]
    ClassificationValidator: type[ClassificationValidator]
    ClassificationValidatorDataDict: type[ClassificationValidatorDataDict]
    InterventionValidator: type[InterventionValidator]
    InterventionValidatorDataDict: type[InterventionValidatorDataDict]
    UnitValidator: type[UnitValidator]
    UnitValidatorDataDict: type[UnitValidatorDataDict]
    FindingsValidator: type[FindingsValidatorModel]
    FindingsValidatorDataDict: type[FindingsValidatorDataDict]
    ExaminationValidator: type[ExaminationValidator]
    ExaminationValidatorDataDict: type[ExaminationValidatorDataDict]


kb_report_template_lookup = KbReportTemplateLookupType(
    ReportTemplate=ReportTemplate,
    ReportTemplateDataDict=ReportTemplateDataDict,
    ReportTemplateGraph=ReportTemplateGraph,
    ReportTemplateGraphDataDict=ReportTemplateGraphDataDict,
    ReportTemplateSection=ReportTemplateSection,
    ReportTemplateSectionDataDict=ReportTemplateSectionDataDict,
    ReportFinding=ReportFinding,
    ReportFindingDataDict=ReportFindingDataDict,
    ClassificationValidator=ClassificationValidator,
    ClassificationValidatorDataDict=ClassificationValidatorDataDict,
    InterventionValidator=InterventionValidator,
    InterventionValidatorDataDict=InterventionValidatorDataDict,
    UnitValidator=UnitValidator,
    UnitValidatorDataDict=UnitValidatorDataDict,
    FindingsValidator=FindingsValidatorModel,
    FindingsValidatorDataDict=FindingsValidatorDataDict,
    ExaminationValidator=ExaminationValidator,
    ExaminationValidatorDataDict=ExaminationValidatorDataDict,
)

kb_report_template_models = Union[
    ReportTemplate,
    ReportTemplateSection,
    ReportFinding,
    ClassificationValidator,
    InterventionValidator,
    UnitValidator,
    FindingsValidator,
    ExaminationValidator,
]

kb_report_template_ddicts = Union[
    ReportTemplateDataDict,
    ReportTemplateGraphDataDict,
    ReportTemplateSectionDataDict,
    ReportFindingDataDict,
    ClassificationValidatorDataDict,
    InterventionValidatorDataDict,
    UnitValidatorDataDict,
    FindingsValidatorDataDict,
    ExaminationValidatorDataDict,
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
    "ReportTemplateSectionField",
    "ReportTemplateSectionFieldDataDict",
    "ReportFinding",
    "ReportFindingDataDict",
    "ReportTemplateClassificationRequirement",
    "ReportTemplateClassificationRequirementDataDict",
    "ReportTemplateFindingRequirement",
    "ReportTemplateFindingRequirementDataDict",
    "ReportTemplateValidators",
    "ReportTemplateValidatorsDataDict",
    "ReportTemplateLifecycleStatusLiteral",
    "ReportTemplateReadinessLiteral",
    "ReportTemplateIssueSeverityLiteral",
    "ReportTemplateIssueScopeLiteral",
    "ReportTemplateReadinessIssue",
    "ReportTemplateReadinessIssueDataDict",
    "ReportTemplateReadinessSummary",
    "ReportTemplateReadinessSummaryDataDict",
    "ClassificationValidator",
    "ClassificationValidatorDataDict",
    "ClassificationValidatorOperator",
    "CLASSIFICATION_VALIDATOR_OPERATORS",
    "ClassificationValidatorPrecedence",
    "CLASSIFICATION_VALIDATOR_PRECEDENCE",
    "ClassificationValidatorQuery",
    "ClassificationValidatorQueryDataDict",
    "ClassificationValidatorCondition",
    "ClassificationValidatorConditionDataDict",
    "ClassificationValidatorConditionClause",
    "ClassificationValidatorHintDataDict",
    "InterventionValidator",
    "InterventionValidatorDataDict",
    "InterventionValidatorOperator",
    "INTERVENTION_VALIDATOR_OPERATORS",
    "InterventionValidatorPrecedence",
    "INTERVENTION_VALIDATOR_PRECEDENCE",
    "InterventionValidatorQuery",
    "InterventionValidatorQueryDataDict",
    "InterventionValidatorCondition",
    "InterventionValidatorConditionDataDict",
    "InterventionValidatorConditionClause",
    "InterventionValidatorHintDataDict",
    "UnitValidator",
    "UnitValidatorDataDict",
    "UnitValidatorOperator",
    "UNIT_VALIDATOR_OPERATORS",
    "UnitValidatorPrecedence",
    "UNIT_VALIDATOR_PRECEDENCE",
    "UnitValidatorQuery",
    "UnitValidatorQueryDataDict",
    "UnitValidatorCondition",
    "UnitValidatorConditionDataDict",
    "UnitValidatorConditionClause",
    "UnitValidatorHintDataDict",
    "FindingsValidator",
    "FindingsValidatorDataDict",
    "FindingsValidatorOperator",
    "FindingsValidatorComparator",
    "FINDINGS_VALIDATOR_OPERATORS",
    "FINDINGS_VALIDATOR_COMPARATORS",
    "DEPRECATED_FINDINGS_VALIDATOR_COMPARATOR_ALIASES",
    "DeprecatedReportTemplateValueWarning",
    "ValidatorRequirementReference",
    "ValidatorRequirementReferenceDataDict",
    "ValidatorRequirementKind",
    "ValidatorRequirementKindLiteral",
    "FindingsValidatorQuery",
    "FindingsValidatorQueryDataDict",
    "FindingsValidatorCondition",
    "FindingsValidatorConditionDataDict",
    "FindingsValidatorConditionClause",
    "FindingsValidatorRequiredClassification",
    "ExaminationValidator",
    "ExaminationValidatorDataDict",
    "RuntimeValidationIssueDataDict",
    "ClassificationValidatorExecutionDataDict",
    "InterventionValidatorExecutionDataDict",
    "ExaminationValidatorDependencyStatusDataDict",
    "FindingsValidatorExecutionDataDict",
    "ExaminationValidatorExecutionDataDict",
    "UnitValidatorExecutionDataDict",
    "ReportTemplateRuntimeValidationResultDataDict",
    "evaluate_classification_validator_runtime",
    "evaluate_findings_validator_runtime",
    "evaluate_intervention_validator_runtime",
    "evaluate_report_template_validators_runtime",
    "evaluate_unit_validator_runtime",
    "build_report_template_graph",
    "validate_report_template_structure",
    "validate_report_template_knowledge_base",
    "KbReportTemplateLookupType",
    "kb_report_template_lookup",
    "kb_report_template_models",
    "kb_report_template_ddicts",
]
