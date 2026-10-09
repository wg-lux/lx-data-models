from importlib import import_module
from typing import TYPE_CHECKING, TypeAlias, TypedDict, Union

from lx_dtypes.models.knowledge_base.validators.ClassificationValidator import (
    CLASSIFICATION_VALIDATOR_OPERATORS,
    CLASSIFICATION_VALIDATOR_PRECEDENCE,
    ClassificationValidator,
    ClassificationValidatorCondition,
    ClassificationValidatorConditionClause,
    ClassificationValidatorOperator,
    ClassificationValidatorPrecedence,
    ClassificationValidatorQuery,
)
from lx_dtypes.models.knowledge_base.validators.ClassificationValidatorDataDict import (
    ClassificationValidatorConditionDataDict,
    ClassificationValidatorDataDict,
    ClassificationValidatorHintDataDict,
    ClassificationValidatorQueryDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ExaminationValidator import (
    ExaminationValidator,
)
from lx_dtypes.models.knowledge_base.validators.ExaminationValidatorDataDict import (
    ExaminationValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.validators.FindingsValidator import (
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
from lx_dtypes.models.knowledge_base.validators.FindingsValidator import (
    FindingsValidator as FindingsValidatorModel,
)
from lx_dtypes.models.knowledge_base.validators.FindingsValidatorDataDict import (
    FindingsValidatorConditionDataDict,
    FindingsValidatorDataDict,
    FindingsValidatorQueryDataDict,
)
from lx_dtypes.models.knowledge_base.validators.FindingTerminologyValidation import (
    validate_reported_findings_against_terminology,
)
from lx_dtypes.models.knowledge_base.validators.InterventionValidator import (
    INTERVENTION_VALIDATOR_OPERATORS,
    INTERVENTION_VALIDATOR_PRECEDENCE,
    InterventionValidator,
    InterventionValidatorCondition,
    InterventionValidatorConditionClause,
    InterventionValidatorOperator,
    InterventionValidatorPrecedence,
    InterventionValidatorQuery,
)
from lx_dtypes.models.knowledge_base.validators.InterventionValidatorDataDict import (
    InterventionValidatorConditionDataDict,
    InterventionValidatorDataDict,
    InterventionValidatorHintDataDict,
    InterventionValidatorQueryDataDict,
)
from lx_dtypes.models.knowledge_base.validators.UnitValidator import (
    UNIT_VALIDATOR_OPERATORS,
    UNIT_VALIDATOR_PRECEDENCE,
    UnitValidator,
    UnitValidatorCondition,
    UnitValidatorConditionClause,
    UnitValidatorOperator,
    UnitValidatorPrecedence,
    UnitValidatorQuery,
)
from lx_dtypes.models.knowledge_base.validators.UnitValidatorDataDict import (
    UnitValidatorConditionDataDict,
    UnitValidatorDataDict,
    UnitValidatorHintDataDict,
    UnitValidatorQueryDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRequirementReference import (
    ValidatorRequirementKind,
    ValidatorRequirementReference,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRequirementReferenceDataDict import (
    ValidatorRequirementKindLiteral,
    ValidatorRequirementReferenceDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRuntimeDataDict import (
    ClassificationValidatorExecutionDataDict,
    ExaminationValidatorDependencyStatusDataDict,
    ExaminationValidatorExecutionDataDict,
    FindingsValidatorExecutionDataDict,
    InterventionValidatorExecutionDataDict,
    ReportTemplateRuntimeValidationResultDataDict,
    RuntimeValidationIssueDataDict,
    UnitValidatorExecutionDataDict,
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

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.fhir.findings import (
        FhirTerminologyValidatedFindingResultDataDict,
        export_reported_findings_to_fhir_observations,
        export_terminology_validated_fhir_observations,
        import_fhir_observations_to_reported_findings,
        import_terminology_validated_fhir_observations,
    )
    from lx_dtypes.models.knowledge_base.validators.ValidatorRuntime import (
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


_RUNTIME_EXPORTS = {
    "evaluate_classification_validator_runtime": "lx_dtypes.models.knowledge_base.validators.ValidatorRuntime",
    "evaluate_findings_validator_runtime": "lx_dtypes.models.knowledge_base.validators.ValidatorRuntime",
    "evaluate_intervention_validator_runtime": "lx_dtypes.models.knowledge_base.validators.ValidatorRuntime",
    "evaluate_report_template_validators_runtime": "lx_dtypes.models.knowledge_base.validators.ValidatorRuntime",
    "evaluate_unit_validator_runtime": "lx_dtypes.models.knowledge_base.validators.ValidatorRuntime",
    "FhirTerminologyValidatedFindingResultDataDict": "lx_dtypes.models.knowledge_base.fhir.findings",
    "export_reported_findings_to_fhir_observations": "lx_dtypes.models.knowledge_base.fhir.findings",
    "export_terminology_validated_fhir_observations": "lx_dtypes.models.knowledge_base.fhir.findings",
    "import_fhir_observations_to_reported_findings": "lx_dtypes.models.knowledge_base.fhir.findings",
    "import_terminology_validated_fhir_observations": "lx_dtypes.models.knowledge_base.fhir.findings",
}


def __getattr__(name: str) -> object:
    if name not in _RUNTIME_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(_RUNTIME_EXPORTS[name]), name)
    globals()[name] = value
    return value
