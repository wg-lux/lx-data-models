from typing import TypeAlias, TypedDict, Union

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
from .ReportConceptCoverage import (
    REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION,
    ReportConceptApplicability,
    ReportConceptApplicabilityStatus,
    ReportConceptCoverage,
    ReportConceptCoverageContractVersion,
    ReportConceptCoverageIdentity,
    ReportConceptCoverageItem,
    ReportConceptCoverageProvenance,
    ReportConceptValidationStatus,
)
from .ReportConceptCoverageBuilder import build_report_concept_coverage
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
from .ReportTemplateCoverage import (
    ReportTemplateCoverageConcept,
    ReportTemplateCoverageFindingSelector,
)
from .ReportTemplateDataDict import (
    ReportTemplateDataDict,
    ReportTemplateValidatorsDataDict,
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
from .ValidatorRuntime import (
    ClassificationValidatorExecutionDataDict,
    ExaminationValidatorDependencyStatusDataDict,
    ExaminationValidatorExecutionDataDict,
    FhirTerminologyValidatedFindingResultDataDict,
    FindingsValidatorExecutionDataDict,
    InterventionValidatorExecutionDataDict,
    ReportTemplateRuntimeValidationResultDataDict,
    RuntimeValidationIssueDataDict,
    UnitValidatorExecutionDataDict,
    evaluate_classification_validator_runtime,
    evaluate_findings_validator_runtime,
    evaluate_intervention_validator_runtime,
    evaluate_report_template_validators_runtime,
    evaluate_unit_validator_runtime,
    export_reported_findings_to_fhir_observations,
    export_terminology_validated_fhir_observations,
    import_fhir_observations_to_reported_findings,
    import_terminology_validated_fhir_observations,
    validate_reported_findings_against_terminology,
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

kb_report_template_models: TypeAlias = Union[
    ReportTemplate,
    ReportTemplateSection,
    ReportFinding,
    ClassificationValidator,
    InterventionValidator,
    UnitValidator,
    FindingsValidatorModel,
    ExaminationValidator,
]

kb_report_template_ddicts: TypeAlias = Union[
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
    "CLASSIFICATION_VALIDATOR_OPERATORS",
    "CLASSIFICATION_VALIDATOR_PRECEDENCE",
    "DEPRECATED_FINDINGS_VALIDATOR_COMPARATOR_ALIASES",
    "FINDINGS_VALIDATOR_COMPARATORS",
    "FINDINGS_VALIDATOR_OPERATORS",
    "INTERVENTION_VALIDATOR_OPERATORS",
    "INTERVENTION_VALIDATOR_PRECEDENCE",
    "REPORT_CONCEPT_COVERAGE_CONTRACT_VERSION",
    "UNIT_VALIDATOR_OPERATORS",
    "UNIT_VALIDATOR_PRECEDENCE",
    "ClassificationValidator",
    "ClassificationValidatorCondition",
    "ClassificationValidatorConditionClause",
    "ClassificationValidatorConditionDataDict",
    "ClassificationValidatorDataDict",
    "ClassificationValidatorExecutionDataDict",
    "ClassificationValidatorHintDataDict",
    "ClassificationValidatorOperator",
    "ClassificationValidatorPrecedence",
    "ClassificationValidatorQuery",
    "ClassificationValidatorQueryDataDict",
    "DeprecatedReportTemplateValueWarning",
    "ExaminationValidator",
    "ExaminationValidatorDataDict",
    "ExaminationValidatorDependencyStatusDataDict",
    "ExaminationValidatorExecutionDataDict",
    "FhirTerminologyValidatedFindingResultDataDict",
    "FindingsValidator",
    "FindingsValidatorComparator",
    "FindingsValidatorCondition",
    "FindingsValidatorConditionClause",
    "FindingsValidatorConditionDataDict",
    "FindingsValidatorDataDict",
    "FindingsValidatorExecutionDataDict",
    "FindingsValidatorOperator",
    "FindingsValidatorQuery",
    "FindingsValidatorQueryDataDict",
    "FindingsValidatorRequiredClassification",
    "InterventionValidator",
    "InterventionValidatorCondition",
    "InterventionValidatorConditionClause",
    "InterventionValidatorConditionDataDict",
    "InterventionValidatorDataDict",
    "InterventionValidatorExecutionDataDict",
    "InterventionValidatorHintDataDict",
    "InterventionValidatorOperator",
    "InterventionValidatorPrecedence",
    "InterventionValidatorQuery",
    "InterventionValidatorQueryDataDict",
    "KbReportTemplateLookupType",
    "ReportConceptApplicability",
    "ReportConceptApplicabilityStatus",
    "ReportConceptCoverage",
    "ReportConceptCoverageContractVersion",
    "ReportConceptCoverageIdentity",
    "ReportConceptCoverageItem",
    "ReportConceptCoverageProvenance",
    "ReportConceptValidationStatus",
    "ReportFinding",
    "ReportFindingDataDict",
    "ReportTemplate",
    "ReportTemplateClassificationRequirement",
    "ReportTemplateClassificationRequirementDataDict",
    "ReportTemplateCoverageConcept",
    "ReportTemplateCoverageFindingSelector",
    "ReportTemplateDataDict",
    "ReportTemplateFindingRequirement",
    "ReportTemplateFindingRequirementDataDict",
    "ReportTemplateGraph",
    "ReportTemplateGraphDataDict",
    "ReportTemplateGraphEdge",
    "ReportTemplateGraphEdgeDataDict",
    "ReportTemplateGraphNode",
    "ReportTemplateGraphNodeDataDict",
    "ReportTemplateIssueScopeLiteral",
    "ReportTemplateIssueSeverityLiteral",
    "ReportTemplateLifecycleStatusLiteral",
    "ReportTemplateReadinessIssue",
    "ReportTemplateReadinessIssueDataDict",
    "ReportTemplateReadinessLiteral",
    "ReportTemplateReadinessSummary",
    "ReportTemplateReadinessSummaryDataDict",
    "ReportTemplateRuntimeValidationResultDataDict",
    "ReportTemplateSection",
    "ReportTemplateSectionDataDict",
    "ReportTemplateSectionField",
    "ReportTemplateSectionFieldDataDict",
    "ReportTemplateStructureIssue",
    "ReportTemplateStructureIssueDataDict",
    "ReportTemplateStructureValidationResult",
    "ReportTemplateStructureValidationResultDataDict",
    "ReportTemplateValidators",
    "ReportTemplateValidatorsDataDict",
    "RuntimeValidationIssueDataDict",
    "UnitValidator",
    "UnitValidatorCondition",
    "UnitValidatorConditionClause",
    "UnitValidatorConditionDataDict",
    "UnitValidatorDataDict",
    "UnitValidatorExecutionDataDict",
    "UnitValidatorHintDataDict",
    "UnitValidatorOperator",
    "UnitValidatorPrecedence",
    "UnitValidatorQuery",
    "UnitValidatorQueryDataDict",
    "ValidatorRequirementKind",
    "ValidatorRequirementKindLiteral",
    "ValidatorRequirementReference",
    "ValidatorRequirementReferenceDataDict",
    "build_report_concept_coverage",
    "build_report_template_graph",
    "evaluate_classification_validator_runtime",
    "evaluate_findings_validator_runtime",
    "evaluate_intervention_validator_runtime",
    "evaluate_report_template_validators_runtime",
    "evaluate_unit_validator_runtime",
    "export_reported_findings_to_fhir_observations",
    "export_terminology_validated_fhir_observations",
    "import_fhir_observations_to_reported_findings",
    "import_terminology_validated_fhir_observations",
    "kb_report_template_ddicts",
    "kb_report_template_lookup",
    "kb_report_template_models",
    "validate_report_template_knowledge_base",
    "validate_report_template_structure",
    "validate_reported_findings_against_terminology",
]
