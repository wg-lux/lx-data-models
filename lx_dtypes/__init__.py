"""Typed clinical data models, terminology, and interoperability contracts.

The package root re-exports the most commonly used public API:

* knowledge-base loading and resolution, such as :func:`load_knowledge_base`;
* canonical terminology contracts, such as :class:`CoreConceptCollection`;
* report templates, their validators, and runtime evaluation functions;
* package-kind inference for legacy packages.

These names are imported lazily on first access, so ``import lx_dtypes`` stays
cheap and does not initialize Django or load knowledge-base data.
Validation entry points live in :mod:`lx_dtypes.evaluation`.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

# Static type checkers and IDEs see the real imports below; at runtime the
# names are resolved on demand by ``__getattr__`` (PEP 562). Keep this block,
# the ``_*_EXPORTS`` sets, and ``__all__`` in sync when adding a public name.
if TYPE_CHECKING:
    from lx_dtypes.models.contracts import (
        CitationCore,
        ClassificationChoiceCore,
        ClassificationChoiceDescriptorCore,
        ClassificationCore,
        ClassificationTypeCore,
        CoreConceptBase,
        CoreConceptCollection,
        ExaminationCore,
        FindingCore,
        FindingTypeCore,
        IndicationCore,
        IndicationTypeCore,
        InformationSourceCore,
        InformationSourceTypeCore,
        InterventionCore,
        InterventionTypeCore,
        KnowledgeBaseIdentity,
        PackageKind,
        PatientExaminationReportDraft,
        UnitCore,
        UnitTypeCore,
        canonical_payload_to_storage,
        core_concept_to_storage,
        kb_to_core_concepts_payload,
        record_to_core_concept,
        records_to_core_concepts,
    )
    from lx_dtypes.models.interface import (
        AmbiguousModuleConfigError,
        KnowledgeBaseIdentityRequiredError,
        KnowledgeBaseLookupTracker,
        KnowledgeBaseRegistryError,
        KnowledgeBaseVersionConflictError,
        KnowledgeBaseVersionNotFoundError,
        ModuleConfigNotFoundError,
        get_knowledge_base_identity,
        load_knowledge_base,
        load_module_config,
        resolve_default_data_root,
        resolve_versioned_input_dirs,
    )
    from lx_dtypes.models.knowledge_base.report_template import (
        ClassificationValidator,
        ClassificationValidatorDataDict,
        ClassificationValidatorExecutionDataDict,
        ExaminationValidator,
        ExaminationValidatorDataDict,
        ExaminationValidatorDependencyStatusDataDict,
        ExaminationValidatorExecutionDataDict,
        FindingsValidator,
        FindingsValidatorDataDict,
        FindingsValidatorExecutionDataDict,
        InterventionValidator,
        InterventionValidatorDataDict,
        InterventionValidatorExecutionDataDict,
        ReportConceptApplicability,
        ReportConceptApplicabilityStatus,
        ReportConceptCoverage,
        ReportConceptCoverageContractVersion,
        ReportConceptCoverageIdentity,
        ReportConceptCoverageItem,
        ReportConceptCoverageProvenance,
        ReportConceptValidationStatus,
        ReportFinding,
        ReportFindingDataDict,
        ReportTemplate,
        ReportTemplateDataDict,
        ReportTemplateGraph,
        ReportTemplateGraphDataDict,
        ReportTemplateGraphEdge,
        ReportTemplateGraphEdgeDataDict,
        ReportTemplateGraphNode,
        ReportTemplateGraphNodeDataDict,
        ReportTemplateRuntimeValidationResultDataDict,
        ReportTemplateSection,
        ReportTemplateSectionDataDict,
        ReportTemplateStructureIssue,
        ReportTemplateStructureIssueDataDict,
        ReportTemplateStructureValidationResult,
        ReportTemplateStructureValidationResultDataDict,
        RuntimeValidationIssueDataDict,
        UnitValidator,
        UnitValidatorDataDict,
        UnitValidatorExecutionDataDict,
        build_report_template_graph,
        evaluate_classification_validator_runtime,
        evaluate_findings_validator_runtime,
        evaluate_intervention_validator_runtime,
        evaluate_report_template_validators_runtime,
        evaluate_unit_validator_runtime,
        validate_report_template_knowledge_base,
        validate_report_template_structure,
    )
    from lx_dtypes.package_kinds import (
        PackageKindInference,
        infer_legacy_package_kind,
    )

_REPORT_TEMPLATE_EXPORTS = {
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
    "ReportConceptApplicability",
    "ReportConceptApplicabilityStatus",
    "ReportConceptCoverage",
    "ReportConceptCoverageContractVersion",
    "ReportConceptCoverageIdentity",
    "ReportConceptCoverageItem",
    "ReportConceptCoverageProvenance",
    "ReportConceptValidationStatus",
    "ClassificationValidator",
    "ClassificationValidatorDataDict",
    "ClassificationValidatorExecutionDataDict",
    "InterventionValidator",
    "InterventionValidatorDataDict",
    "InterventionValidatorExecutionDataDict",
    "UnitValidator",
    "UnitValidatorDataDict",
    "UnitValidatorExecutionDataDict",
    "FindingsValidator",
    "FindingsValidatorDataDict",
    "FindingsValidatorExecutionDataDict",
    "ExaminationValidator",
    "ExaminationValidatorDataDict",
    "ExaminationValidatorDependencyStatusDataDict",
    "ExaminationValidatorExecutionDataDict",
    "ReportTemplateRuntimeValidationResultDataDict",
    "RuntimeValidationIssueDataDict",
    "evaluate_findings_validator_runtime",
    "evaluate_classification_validator_runtime",
    "evaluate_intervention_validator_runtime",
    "evaluate_report_template_validators_runtime",
    "evaluate_unit_validator_runtime",
    "build_report_template_graph",
    "validate_report_template_structure",
    "validate_report_template_knowledge_base",
}

_CONTRACT_EXPORTS = {
    "CoreConceptBase",
    "ClassificationCore",
    "ClassificationTypeCore",
    "ClassificationChoiceCore",
    "ClassificationChoiceDescriptorCore",
    "ExaminationCore",
    "FindingCore",
    "FindingTypeCore",
    "IndicationCore",
    "IndicationTypeCore",
    "InterventionCore",
    "InterventionTypeCore",
    "UnitCore",
    "UnitTypeCore",
    "InformationSourceCore",
    "InformationSourceTypeCore",
    "CitationCore",
    "CoreConceptCollection",
    "KnowledgeBaseIdentity",
    "PackageKind",
    "PatientExaminationReportDraft",
    "record_to_core_concept",
    "records_to_core_concepts",
    "core_concept_to_storage",
    "kb_to_core_concepts_payload",
    "canonical_payload_to_storage",
}

_INTERFACE_EXPORTS = {
    "AmbiguousModuleConfigError",
    "KnowledgeBaseIdentityRequiredError",
    "KnowledgeBaseLookupTracker",
    "KnowledgeBaseRegistryError",
    "KnowledgeBaseVersionConflictError",
    "KnowledgeBaseVersionNotFoundError",
    "ModuleConfigNotFoundError",
    "get_knowledge_base_identity",
    "load_knowledge_base",
    "load_module_config",
    "resolve_default_data_root",
    "resolve_versioned_input_dirs",
}

_PACKAGE_KIND_EXPORTS = {
    "PackageKindInference",
    "infer_legacy_package_kind",
}


def __getattr__(name: str) -> Any:
    """Import a public name from its defining subpackage on first access.

    Python caches the defining module after the first import, so later
    lookups of the same name are cheap.
    """
    if name in _PACKAGE_KIND_EXPORTS:
        module = import_module("lx_dtypes.package_kinds")
        return getattr(module, name)

    if name in _REPORT_TEMPLATE_EXPORTS:
        module = import_module("lx_dtypes.models.knowledge_base.report_template")
        return getattr(module, name)

    if name in _CONTRACT_EXPORTS:
        module = import_module("lx_dtypes.models.contracts")
        return getattr(module, name)

    if name in _INTERFACE_EXPORTS:
        module = import_module("lx_dtypes.models.interface")
        return getattr(module, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AmbiguousModuleConfigError",
    "CitationCore",
    "ClassificationChoiceCore",
    "ClassificationChoiceDescriptorCore",
    "ClassificationCore",
    "ClassificationTypeCore",
    "ClassificationValidator",
    "ClassificationValidatorDataDict",
    "ClassificationValidatorExecutionDataDict",
    "CoreConceptBase",
    "CoreConceptCollection",
    "ExaminationCore",
    "ExaminationValidator",
    "ExaminationValidatorDataDict",
    "ExaminationValidatorDependencyStatusDataDict",
    "ExaminationValidatorExecutionDataDict",
    "FindingCore",
    "FindingTypeCore",
    "FindingsValidator",
    "FindingsValidatorDataDict",
    "FindingsValidatorExecutionDataDict",
    "IndicationCore",
    "IndicationTypeCore",
    "InformationSourceCore",
    "InformationSourceTypeCore",
    "InterventionCore",
    "InterventionTypeCore",
    "InterventionValidator",
    "InterventionValidatorDataDict",
    "InterventionValidatorExecutionDataDict",
    "KnowledgeBaseIdentity",
    "KnowledgeBaseIdentityRequiredError",
    "KnowledgeBaseLookupTracker",
    "KnowledgeBaseRegistryError",
    "KnowledgeBaseVersionConflictError",
    "KnowledgeBaseVersionNotFoundError",
    "ModuleConfigNotFoundError",
    "PackageKind",
    "PackageKindInference",
    "PatientExaminationReportDraft",
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
    "ReportTemplateDataDict",
    "ReportTemplateGraph",
    "ReportTemplateGraphDataDict",
    "ReportTemplateGraphEdge",
    "ReportTemplateGraphEdgeDataDict",
    "ReportTemplateGraphNode",
    "ReportTemplateGraphNodeDataDict",
    "ReportTemplateRuntimeValidationResultDataDict",
    "ReportTemplateSection",
    "ReportTemplateSectionDataDict",
    "ReportTemplateStructureIssue",
    "ReportTemplateStructureIssueDataDict",
    "ReportTemplateStructureValidationResult",
    "ReportTemplateStructureValidationResultDataDict",
    "RuntimeValidationIssueDataDict",
    "UnitCore",
    "UnitTypeCore",
    "UnitValidator",
    "UnitValidatorDataDict",
    "UnitValidatorExecutionDataDict",
    "build_report_template_graph",
    "canonical_payload_to_storage",
    "core_concept_to_storage",
    "evaluate_classification_validator_runtime",
    "evaluate_findings_validator_runtime",
    "evaluate_intervention_validator_runtime",
    "evaluate_report_template_validators_runtime",
    "evaluate_unit_validator_runtime",
    "get_knowledge_base_identity",
    "infer_legacy_package_kind",
    "kb_to_core_concepts_payload",
    "load_knowledge_base",
    "load_module_config",
    "record_to_core_concept",
    "records_to_core_concepts",
    "resolve_default_data_root",
    "resolve_versioned_input_dirs",
    "validate_report_template_knowledge_base",
    "validate_report_template_structure",
]
