"""Knowledge-base storage, provenance, lookup, loading and serialization.

Reporting, ledger admissibility and exchange methods delegate to focused adapters
while retaining the public KnowledgeBase API.
"""

import warnings
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Self,
    TypedDict,
    cast,
)

import yaml
from pydantic import BaseModel, Field, PrivateAttr

from lx_dtypes.language import DEFAULT_LANGUAGE
from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.contracts.finding_extraction import FindingTextExtractor
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.validation import SemanticValidationError
from lx_dtypes.models.interface.KnowledgeBaseAdmissibility import (
    KnowledgeBaseAdmissibility,
)
from lx_dtypes.models.interface.KnowledgeBaseAdmissibility import (
    # Public import path kept stable after the split; `X as X` re-exports (PEP 484).
    SemanticAdmissibilityError as SemanticAdmissibilityError,  # noqa: PLC0414
)
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.interface.KnowledgeBaseInterop import KnowledgeBaseInterop
from lx_dtypes.models.interface.KnowledgeBaseReporting import KnowledgeBaseReporting
from lx_dtypes.models.interface.LookupTracker import KnowledgeBaseLookupTracker
from lx_dtypes.models.knowledge_base.center.center_employee_list import (
    CenterEmployeeList,
    CenterEmployeeListDataDict,
)
from lx_dtypes.models.knowledge_base.citation.Citation import Citation
from lx_dtypes.models.knowledge_base.citation.CitationDataDict import CitationDataDict
from lx_dtypes.models.knowledge_base.classification.Classification import (
    Classification,
)
from lx_dtypes.models.knowledge_base.classification.ClassificationDataDict import (
    ClassificationDataDict,
)
from lx_dtypes.models.knowledge_base.classification.ClassificationType import (
    ClassificationType,
)
from lx_dtypes.models.knowledge_base.classification.ClassificationTypeDataDict import (
    ClassificationTypeDataDict,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoiceDataDict import (
    ClassificationChoiceDataDict,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptorDataDict import (
    ClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.knowledge_base.electrical_curve_profile import (
    ElectricalCurveProfile,
    ElectricalCurveProfileDataDict,
)
from lx_dtypes.models.knowledge_base.examination.Examination import Examination
from lx_dtypes.models.knowledge_base.examination.ExaminationDataDict import (
    ExaminationDataDict,
)
from lx_dtypes.models.knowledge_base.examination.ExaminationType import ExaminationType
from lx_dtypes.models.knowledge_base.examination.ExaminationTypeDataDict import (
    ExaminationTypeDataDict,
)
from lx_dtypes.models.knowledge_base.fhir.findings import (
    FhirTerminologyValidatedFindingResultDataDict,
)
from lx_dtypes.models.knowledge_base.finding._Finding import Finding
from lx_dtypes.models.knowledge_base.finding._FindingType import FindingType
from lx_dtypes.models.knowledge_base.finding.FindingDataDict import FindingDataDict
from lx_dtypes.models.knowledge_base.finding.FindingTypeDataDict import (
    FindingTypeDataDict,
)
from lx_dtypes.models.knowledge_base.indication.Indication import Indication
from lx_dtypes.models.knowledge_base.indication.IndicationDataDict import (
    IndicationDataDict,
)
from lx_dtypes.models.knowledge_base.indication.IndicationType import IndicationType
from lx_dtypes.models.knowledge_base.indication.IndicationTypeDataDict import (
    IndicationTypeDataDict,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSource import (
    InformationSource,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceDataDict import (
    InformationSourceDataDict,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceType import (
    InformationSourceType,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceTypeDataDict import (
    InformationSourceTypeDataDict,
)
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.intervention.InterventionDataDict import (
    InterventionDataDict,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionType import (
    InterventionType,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionTypeDataDict import (
    InterventionTypeDataDict,
)
from lx_dtypes.models.knowledge_base.pydantic_main import (
    KB_DDICTS,
    KB_MODEL_NAMES_LITERAL,
    KB_MODEL_NAMES_ORDERED,
    KB_MODELS,
    knowledge_base_models_lookup,
)
from lx_dtypes.models.knowledge_base.reference_catalog import (
    ReferenceCatalog,
    ReferenceCatalogDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import (
    ReportFinding,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFindingDataDict import (
    ReportFindingDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateDataDict import (
    ReportTemplateDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSection import (
    ReportTemplateSection,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSectionDataDict import (
    ReportTemplateSectionDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.TemplateReadiness import (
    ReportTemplateLifecycleStatusLiteral,
)
from lx_dtypes.models.knowledge_base.study_preset import (
    StudyPreset,
    StudyPresetDataDict,
)
from lx_dtypes.models.knowledge_base.time_reference import (
    TimeReference,
    TimeReferenceDataDict,
)
from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitDataDict import UnitDataDict
from lx_dtypes.models.knowledge_base.unit.UnitType import UnitType
from lx_dtypes.models.knowledge_base.unit.UnitTypeDataDict import UnitTypeDataDict
from lx_dtypes.models.knowledge_base.validators.ClassificationValidator import (
    ClassificationValidator,
)
from lx_dtypes.models.knowledge_base.validators.ClassificationValidatorDataDict import (
    ClassificationValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ExaminationValidator import (
    ExaminationValidator,
)
from lx_dtypes.models.knowledge_base.validators.ExaminationValidatorDataDict import (
    ExaminationValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.validators.FindingsValidator import (
    FindingsValidator,
)
from lx_dtypes.models.knowledge_base.validators.FindingsValidatorDataDict import (
    FindingsValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.validators.InterventionValidator import (
    InterventionValidator,
)
from lx_dtypes.models.knowledge_base.validators.InterventionValidatorDataDict import (
    InterventionValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.validators.RuntimeIssues import (
    RuntimeValidationLanguage,
)
from lx_dtypes.models.knowledge_base.validators.UnitValidator import (
    UnitValidator,
)
from lx_dtypes.models.knowledge_base.validators.UnitValidatorDataDict import (
    UnitValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRuntimeDataDict import (
    ClassificationValidatorExecutionDataDict,
    ExaminationValidatorExecutionDataDict,
    FindingsValidatorExecutionDataDict,
    InterventionValidatorExecutionDataDict,
    ReportTemplateRuntimeValidationResultDataDict,
    UnitValidatorExecutionDataDict,
)
from lx_dtypes.utils.parser import (
    CLINICAL_CONCEPT_MODELS,
    camel_to_snake,
    parse_shallow_object_with_meta,
    snake_to_camel,
)
from lx_dtypes.utils.report_template_registry import (
    load_report_template_registry,
    registry_path_for_module,
)

if TYPE_CHECKING:
    from lx_dtypes.models.interface.Ledger import Ledger
    from lx_dtypes.models.ledger.p_electrical_application import (
        PElectricalApplication,
        PElectricalCurveComparison,
    )
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
    from lx_dtypes.models.ledger.p_time_offset import PTimeOffset


class ReportTemplateConceptWarning(UserWarning):
    """A reporting/study package defines concepts instead of referencing terminology."""

    def __init__(
        self,
        message: str,
        *,
        source_file: Path,
        line: int,
        column: int,
        definitions: tuple["ReportTemplateConceptWarning", ...] = (),
    ) -> None:
        super().__init__(message)
        self.source_file = source_file
        self.line = line
        self.column = column
        self.definitions = definitions


class KnowledgeBaseDDict(AppBaseModelUUIDTagsDataDict):
    time_reference: dict[str, TimeReferenceDataDict]
    electrical_curve_profile: dict[str, ElectricalCurveProfileDataDict]
    study_preset: dict[str, StudyPresetDataDict]
    reference_catalog: dict[str, ReferenceCatalogDataDict]
    center_employee_list: dict[str, CenterEmployeeListDataDict]
    config: KnowledgeBaseConfig
    citation: dict[str, CitationDataDict]
    classification: dict[str, ClassificationDataDict]
    classification_type: dict[str, ClassificationTypeDataDict]
    classification_choice: dict[str, ClassificationChoiceDataDict]
    classification_choice_descriptor: dict[str, ClassificationChoiceDescriptorDataDict]
    examination: dict[str, ExaminationDataDict]
    examination_type: dict[str, ExaminationTypeDataDict]
    finding: dict[str, FindingDataDict]
    finding_type: dict[str, FindingTypeDataDict]
    indication: dict[str, IndicationDataDict]
    indication_type: dict[str, IndicationTypeDataDict]
    intervention: dict[str, InterventionDataDict]
    intervention_type: dict[str, InterventionTypeDataDict]
    unit_type: dict[str, UnitTypeDataDict]
    unit: dict[str, UnitDataDict]
    information_source: dict[str, InformationSourceDataDict]
    information_source_type: dict[str, InformationSourceTypeDataDict]
    report_template_section: dict[str, ReportTemplateSectionDataDict]
    report_finding: dict[str, ReportFindingDataDict]
    classification_validator: dict[str, ClassificationValidatorDataDict]
    intervention_validator: dict[str, InterventionValidatorDataDict]
    unit_validator: dict[str, UnitValidatorDataDict]
    findings_validator: dict[str, FindingsValidatorDataDict]
    examination_validator: dict[str, ExaminationValidatorDataDict]
    report_template: dict[str, ReportTemplateDataDict]
    # labelset -> links to labels
    # label -> links to finding, intervention, classification + classificationchoice, examination


YAML_IMPORT_SKIP_FIELDS = [
    "config",
    "uuid",
    "source_file",
    "created_at",
    "updated_at",
    "report_template_lifecycle_status",
]


class KnowledgeBaseRecordList(TypedDict):
    time_references: list[TimeReferenceDataDict]
    electrical_curve_profiles: list[ElectricalCurveProfileDataDict]
    study_presets: list[StudyPresetDataDict]
    reference_catalogs: list[ReferenceCatalogDataDict]
    center_employee_lists: list[CenterEmployeeListDataDict]
    citations: list[CitationDataDict]
    classifications: list[ClassificationDataDict]
    classification_types: list[ClassificationTypeDataDict]
    classification_choices: list[ClassificationChoiceDataDict]
    classification_choice_descriptors: list[ClassificationChoiceDescriptorDataDict]
    examinations: list[ExaminationDataDict]
    examination_types: list[ExaminationTypeDataDict]
    findings: list[FindingDataDict]
    finding_types: list[FindingTypeDataDict]
    indications: list[IndicationDataDict]
    indication_types: list[IndicationTypeDataDict]
    interventions: list[InterventionDataDict]
    intervention_types: list[InterventionTypeDataDict]
    units: list[UnitDataDict]
    unit_types: list[UnitTypeDataDict]
    information_sources: list[InformationSourceDataDict]
    information_source_types: list[InformationSourceTypeDataDict]
    report_template_sections: list[ReportTemplateSectionDataDict]
    report_findings: list[ReportFindingDataDict]
    classification_validators: list[ClassificationValidatorDataDict]
    intervention_validators: list[InterventionValidatorDataDict]
    unit_validators: list[UnitValidatorDataDict]
    findings_validators: list[FindingsValidatorDataDict]
    examination_validators: list[ExaminationValidatorDataDict]
    report_templates: list[ReportTemplateDataDict]


class KnowledgeBase(AppBaseModelUUIDTags):
    time_reference: dict[str, TimeReference] = Field(default_factory=dict)
    electrical_curve_profile: dict[str, ElectricalCurveProfile] = Field(
        default_factory=dict
    )
    study_preset: dict[str, StudyPreset] = Field(default_factory=dict)
    reference_catalog: dict[str, ReferenceCatalog] = Field(default_factory=dict)
    center_employee_list: dict[str, CenterEmployeeList] = Field(default_factory=dict)
    config: KnowledgeBaseConfig
    citation: dict[str, Citation] = Field(default_factory=dict)
    classification: dict[str, Classification] = Field(default_factory=dict)
    classification_type: dict[str, ClassificationType] = Field(default_factory=dict)
    classification_choice: dict[str, ClassificationChoice] = Field(default_factory=dict)
    classification_choice_descriptor: dict[str, ClassificationChoiceDescriptor] = Field(
        default_factory=dict
    )
    examination: dict[str, Examination] = Field(default_factory=dict)
    examination_type: dict[str, ExaminationType] = Field(default_factory=dict)
    finding: dict[str, Finding] = Field(default_factory=dict)
    finding_type: dict[str, FindingType] = Field(default_factory=dict)
    indication: dict[str, Indication] = Field(default_factory=dict)
    indication_type: dict[str, IndicationType] = Field(default_factory=dict)
    intervention: dict[str, Intervention] = Field(default_factory=dict)
    intervention_type: dict[str, InterventionType] = Field(default_factory=dict)
    unit_type: dict[str, UnitType] = Field(default_factory=dict)
    unit: dict[str, Unit] = Field(default_factory=dict)
    information_source: dict[str, InformationSource] = Field(default_factory=dict)
    information_source_type: dict[str, InformationSourceType] = Field(
        default_factory=dict
    )
    report_template_section: dict[str, ReportTemplateSection] = Field(
        default_factory=dict
    )
    report_finding: dict[str, ReportFinding] = Field(default_factory=dict)
    classification_validator: dict[str, ClassificationValidator] = Field(
        default_factory=dict
    )
    intervention_validator: dict[str, InterventionValidator] = Field(
        default_factory=dict
    )
    unit_validator: dict[str, UnitValidator] = Field(default_factory=dict)
    findings_validator: dict[str, FindingsValidator] = Field(default_factory=dict)
    examination_validator: dict[str, ExaminationValidator] = Field(default_factory=dict)
    report_template: dict[str, ReportTemplate] = Field(default_factory=dict)
    report_template_lifecycle_status: dict[
        str, ReportTemplateLifecycleStatusLiteral
    ] = Field(default_factory=dict, exclude=True)
    _lookup_tracker: KnowledgeBaseLookupTracker = PrivateAttr(
        default_factory=KnowledgeBaseLookupTracker
    )

    _definition_locations: dict[tuple[str, str], tuple[Path, int, int]] = PrivateAttr(
        default_factory=dict
    )
    _reporting_modules: set[str] = PrivateAttr(default_factory=set)
    _resolved_module_configs: dict[str, KnowledgeBaseConfig] = PrivateAttr(
        default_factory=dict
    )

    def _definition_identity(self, definition: KB_MODELS) -> KnowledgeBaseIdentity:
        """Resolved module/version of the module that owns ``definition``."""
        configs = self._resolved_module_configs or {self.config.name: self.config}
        config = configs.get(definition.kb_module_name)
        if config is None:
            # A configuration fault, not an observation finding: never advisory.
            raise ValueError(
                f"Module '{definition.kb_module_name}' has no resolved version"
            )
        return config.knowledge_base_identity

    def validate_time_offset(self, observation: "PTimeOffset") -> None:
        """Resolve the semantic reference and check its pinned module/version."""
        reference = self.time_reference.get(observation.time_reference)
        if reference is None:
            raise SemanticValidationError("terminology.time_reference_unknown")
        observation.validate_reference(reference, self._definition_identity(reference))

    def validate_electrical_observation(
        self, observation: "PElectricalApplication | PElectricalCurveComparison"
    ) -> None:
        """Resolve the electrical curve profile and check its pinned module/version."""
        profile = self.electrical_curve_profile.get(
            observation.electrical_curve_profile
        )
        if profile is None:
            raise SemanticValidationError(
                "terminology.electrical_curve_profile_unknown"
            )
        observation.validate_profile(profile, self._definition_identity(profile))

    @property
    def is_reporting_package(self) -> bool:
        """Whether this module owns or inherits reporting/study definitions."""
        return self.config.name in self._reporting_modules

    def warn_local_concept_definitions(
        self, *, reporting_context: bool = False
    ) -> None:
        """Warn only for this module's concepts, before importing dependencies."""
        if not (reporting_context or self.is_reporting_package):
            return
        self._reporting_modules.add(self.config.name)
        definitions: list[ReportTemplateConceptWarning] = []
        for (model_name, name), location in self._definition_locations.items():
            if model_name not in CLINICAL_CONCEPT_MODELS:
                continue
            record: KB_MODELS = getattr(self, model_name)[name]
            if record.kb_module_name != self.config.name:
                continue
            file, line, column = location
            definitions.append(
                ReportTemplateConceptWarning(
                    f"{file}:{line}:{column}: '{model_name}' definition '{name}' "
                    f"in reporting/study module '{self.config.name}'. Move this custom "
                    "definition into a terminology package and reference it through "
                    "depends_on. If it already exists in guideline terminology, remove "
                    "this copy and reference that definition. See "
                    "docs/guides/dtypes-package-structure.md and "
                    "lx_dtypes/data/definitions.yml for terminology package manifests.",
                    source_file=file,
                    line=line,
                    column=column,
                )
            )
        if not definitions:
            return
        first = definitions[0]
        warning = first
        if len(definitions) > 1:
            warning = ReportTemplateConceptWarning(
                f"{self.config.name}@{self.config.version}: {len(definitions)} clinical "
                "concept definitions in a reporting/study module. "
                f"First definition: {first} "
                "All definitions are available in warning.definitions and package lint diagnostics.",
                source_file=first.source_file,
                line=first.line,
                column=first.column,
                definitions=tuple(definitions),
            )
        warnings.warn(warning, stacklevel=2)

    def definition_source(
        self, model_name: str, name: str
    ) -> tuple[Path, int, int] | None:
        """Return the original YAML location, including imported definitions."""
        return self._definition_locations.get((model_name, name))

    def _definition_location(
        self, model_name: str, name: str, record: KB_MODELS
    ) -> str:
        location = self._definition_locations.get((model_name, name))
        if location is None:
            return str(record.source_file or "<source unavailable>")
        file, line, column = location
        return f"{file}:{line}:{column}"

    def _lookup_required(
        self,
        *,
        collection_name: str,
        key: str,
        source: str = "knowledge_base",
    ) -> Any:
        collection = cast(dict[str, Any], getattr(self, collection_name))
        found = key in collection
        self._lookup_tracker.record_lookup(
            source=source,
            target=collection_name,
            key=key,
            found=found,
        )
        return collection[key]

    def _lookup_optional(
        self,
        *,
        collection_name: str,
        key: str,
        source: str = "knowledge_base",
    ) -> Any:
        collection = cast(dict[str, Any], getattr(self, collection_name))
        found = key in collection
        self._lookup_tracker.record_lookup(
            source=source,
            target=collection_name,
            key=key,
            found=found,
        )
        return collection.get(key)

    def reset_lookup_tracker(self) -> None:
        self._lookup_tracker.reset()

    def get_lookup_tracker_summary(self) -> dict[str, Any]:
        return self._lookup_tracker.as_summary()

    def export_lookup_tracker_mermaid(self) -> str:
        return self._lookup_tracker.export_mermaid_graph()

    def export_lookup_tracker_dot(self) -> str:
        return self._lookup_tracker.export_dot_graph()

    def compare_lookup_performance_to_snomed(
        self,
        *,
        snomed_lookup_count: int,
        lx_elapsed_seconds: float | None = None,
        snomed_elapsed_seconds: float | None = None,
    ) -> dict[str, Any]:
        return self._lookup_tracker.compare_to_snomed(
            snomed_lookup_count=snomed_lookup_count,
            lx_elapsed_seconds=lx_elapsed_seconds,
            snomed_elapsed_seconds=snomed_elapsed_seconds,
        )

    def get_classification(self, name: str) -> Classification:
        """
        Retrieve a Classification by its name from this knowledge base.

        Parameters:
            name (str): The classification's unique name/key.

        Returns:
            Classification: The Classification instance identified by `name`.
        """
        return cast(
            Classification,
            self._lookup_required(collection_name="classification", key=name),
        )

    def get_classification_type(self, name: str) -> ClassificationType:
        """
        Retrieve a ClassificationType by its name.

        Returns:
            The ClassificationType with the given name.
        """
        return cast(
            ClassificationType,
            self._lookup_required(collection_name="classification_type", key=name),
        )

    def get_classification_choice(self, name: str) -> ClassificationChoice:
        """
        Retrieve a ClassificationChoice by its registered name.

        Parameters:
            name (str): The unique name/key of the classification choice to retrieve.

        Returns:
            ClassificationChoice: The classification choice instance associated with `name`.
        """
        return cast(
            ClassificationChoice,
            self._lookup_required(collection_name="classification_choice", key=name),
        )

    def get_classification_choice_descriptor(
        self, name: str
    ) -> ClassificationChoiceDescriptor:
        """
        Retrieve a ClassificationChoiceDescriptor by its name.

        Parameters:
            name (str): The name of the classification choice descriptor to retrieve.

        Returns:
            ClassificationChoiceDescriptor: The descriptor matching `name`.
        """
        return cast(
            ClassificationChoiceDescriptor,
            self._lookup_required(
                collection_name="classification_choice_descriptor", key=name
            ),
        )

    def get_examination(self, name: str) -> Examination:
        """
        Retrieve an Examination by its name.

        Returns:
            Examination: The Examination instance associated with the given name.
        """
        return cast(
            Examination,
            self._lookup_required(collection_name="examination", key=name),
        )

    def get_examination_type(self, name: str) -> ExaminationType:
        """
        Retrieve an examination type by its name.

        Parameters:
            name (str): The lookup key of the examination type.

        Returns:
            ExaminationType: The ExaminationType with the given name.

        Raises:
            KeyError: If no examination type with the specified name exists.
        """
        return cast(
            ExaminationType,
            self._lookup_required(collection_name="examination_type", key=name),
        )

    def get_finding(self, name: str) -> Finding:
        """
        Retrieve a Finding by its name.

        Parameters:
            name (str): The name (key) of the finding to retrieve.

        Returns:
            Finding: The Finding instance corresponding to `name`.

        Raises:
            KeyError: If no finding with the given `name` exists.
        """
        return cast(
            Finding,
            self._lookup_required(collection_name="finding", key=name),
        )

    def get_finding_type(self, name: str) -> FindingType:
        """
        Retrieve a FindingType by its name.

        Parameters:
            name (str): The finding type's name (key) to look up.

        Returns:
            FindingType: The FindingType instance matching `name`.

        Raises:
            KeyError: If no FindingType with `name` exists in the knowledge base.
        """
        return cast(
            FindingType,
            self._lookup_required(collection_name="finding_type", key=name),
        )

    def get_indication(self, name: str) -> Indication:
        """
        Retrieve an Indication by its name.

        Parameters:
            name (str): The unique name/key of the indication to retrieve.

        Returns:
            Indication: The Indication instance matching the provided name.
        """
        return cast(
            Indication,
            self._lookup_required(collection_name="indication", key=name),
        )

    def get_indication_type(self, name: str) -> IndicationType:
        """
        Retrieve an IndicationType by its name.

        Returns:
            The IndicationType with the given name.
        """
        return cast(
            IndicationType,
            self._lookup_required(collection_name="indication_type", key=name),
        )

    def get_intervention(self, name: str) -> Intervention:
        """
        Retrieve an Intervention by its name from the knowledge base.

        Parameters:
            name (str): The intervention's name (dictionary key) to look up.

        Returns:
            Intervention: The Intervention instance with the given name.
        """
        return cast(
            Intervention,
            self._lookup_required(collection_name="intervention", key=name),
        )

    def get_intervention_type(self, name: str) -> InterventionType:
        """
        Retrieve an InterventionType by its name.

        Parameters:
            name (str): The intervention type's name to look up.

        Returns:
            InterventionType: The InterventionType instance matching `name`.

        Raises:
            KeyError: If no intervention type with the given name exists.
        """
        return cast(
            InterventionType,
            self._lookup_required(collection_name="intervention_type", key=name),
        )

    def get_unit_type(self, name: str) -> UnitType:
        """
        Retrieve a UnitType from the knowledge base by its name.

        Parameters:
            name (str): The name of the unit type to retrieve.

        Returns:
            UnitType: The unit type with the given name.
        """
        return cast(
            UnitType,
            self._lookup_required(collection_name="unit_type", key=name),
        )

    def get_unit(self, name: str) -> Unit:
        """
        Retrieve the Unit with the given name from the knowledge base.

        Parameters:
            name (str): The unit's identifier as stored in the knowledge base.

        Returns:
            Unit: The Unit instance corresponding to the provided name.
        """
        return cast(
            Unit,
            self._lookup_required(collection_name="unit", key=name),
        )

    def get_report_template(self, name: str) -> ReportTemplate:
        """
        Retrieve a ReportTemplate by name.

        Parameters:
            name (str): The report template name.

        Returns:
            ReportTemplate: The template with the given name.
        """
        return cast(
            ReportTemplate,
            self._lookup_required(collection_name="report_template", key=name),
        )

    def get_report_template_lifecycle_status(
        self, name: str
    ) -> ReportTemplateLifecycleStatusLiteral:
        status = self._lookup_optional(
            collection_name="report_template_lifecycle_status",
            key=name,
            source="knowledge_base",
        )
        if status is None:
            return "published"
        return cast(ReportTemplateLifecycleStatusLiteral, status)

    def published_report_template_names(self) -> list[str]:
        return [
            template_name
            for template_name in self.report_template
            if self.get_report_template_lifecycle_status(template_name) == "published"
        ]

    @property
    def ddict_class(self) -> type[KnowledgeBaseDDict]:
        """
        Return the DataDict class used to build serialized dictionary representations of this KnowledgeBase.

        Returns:
            The `KnowledgeBaseDDict` class used for ddict construction.
        """
        return KnowledgeBaseDDict

    @property
    def ddict(self) -> KnowledgeBaseDDict:
        """
        Create a data-dictionary representation of the knowledge base.

        Returns:
            KnowledgeBaseDDict: A data-dictionary (plain-Python) representation of the model suitable for serialization and export.
        """
        return self.ddict_class(**self.model_dump())

    @classmethod
    def create_from_config(
        cls, config: "KnowledgeBaseConfig", *, warn_concepts: bool = True
    ) -> "KnowledgeBase":
        """
        Create a KnowledgeBase instance from a KnowledgeBaseConfig and populate its module entries from YAML files referenced by the config.

        Parameters:
            config (KnowledgeBaseConfig): Configuration describing the knowledge base and the data source(s). The config's data provider is used to locate and parse submodule YAML files.

        Returns:
            KnowledgeBase: A KnowledgeBase validated from the provided config and populated with parsed model objects from the config's YAML submodules.

        Raises:
            ValueError: If a parsed object corresponds to a model name that does not exist on the KnowledgeBase class.
        """
        name = config.name
        # source_file = config.source_file
        # assert source_file is not None, "Config must have source_file set." # Can be removed?
        kb_source_dict: dict[str, KnowledgeBaseConfig | Path] = {
            "config": config,
            # "source_file": source_file,  # Can be removed?
        }
        kb = cls.model_validate(kb_source_dict)
        registry_path: Path | None = None
        if config.source_file is not None:
            kb.report_template_lifecycle_status = load_report_template_registry(
                config.source_file.parent
            )
            registry_path = registry_path_for_module(
                config.source_file.parent
            ).resolve()
        seen_records = kb._definition_locations
        data = config.data
        submodule_files = sorted(
            set(data.get_files_with_suffix(".yaml"))
            | set(data.get_files_with_suffix(".yml")),
            key=lambda path: (path.name, str(path)),
        )
        for sm_file in submodule_files:
            if registry_path is not None and sm_file.resolve() == registry_path:
                continue
            parsed_entries = parse_shallow_object_with_meta(
                sm_file, kb_module_name=name
            )
            # Hard error for duplicate module names in the same KnowledgeBase -> Used by Parser
            for parsed_entry in parsed_entries:
                parsed_object = parsed_entry.parsed_object
                model_name = camel_to_snake(type(parsed_object).__name__)
                object_name = parsed_object.name
                duplicate_key = (model_name, object_name)
                existing_ref = seen_records.get(duplicate_key)
                if existing_ref is not None:
                    prev_file, prev_line, prev_column = existing_ref
                    raise ValueError(
                        f"Duplicate '{model_name}' name '{object_name}' in module "
                        f"'{name}': {prev_file}:{prev_line}:{prev_column} and "
                        f"{parsed_entry.source_file}:{parsed_entry.line}:"
                        f"{parsed_entry.column}"
                    )
                seen_records[duplicate_key] = (
                    parsed_entry.source_file,
                    parsed_entry.line,
                    parsed_entry.column,
                )
                if not hasattr(kb, model_name):
                    raise ValueError(f"KnowledgeBase has no attribute '{model_name}'")
                model_dict: dict[str, KB_MODELS] = getattr(kb, model_name)
                model_dict[object_name] = parsed_object

                # set the updated dict back to the kb
                setattr(kb, model_name, model_dict)
        if (
            kb.report_template
            or kb.report_template_section
            or kb.report_finding
            or kb.study_preset
            or (
                config.source_file is not None
                and config.source_file.parent.parent.name == "report_templates"
            )
        ):
            kb._reporting_modules.add(name)
        if warn_concepts:
            kb.warn_local_concept_definitions()
        return kb

    @classmethod
    def create_from_yaml(cls, yaml_path: Path) -> Self:
        """
        Create a KnowledgeBase instance from a YAML file.

        Loads the YAML file at yaml_path and validates its contents into a KnowledgeBase.

        Returns:
            KnowledgeBase: The validated KnowledgeBase instance constructed from the YAML file.
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            data_dict = yaml.safe_load(f)

        kb = cls.model_validate(data_dict)
        return kb

    def resolved_module_configs(self) -> dict[str, KnowledgeBaseConfig]:
        """Copies of the configs this KB was loaded from, keyed by module name.

        ``modules`` of each copy lists that module's resolved closure.
        """
        configs = self._resolved_module_configs or {self.config.name: self.config}
        return {name: config.model_copy(deep=True) for name, config in configs.items()}

    def composed_module_names(self) -> frozenset[str]:
        """Return the root module and the modules it composes through ``modules``.

        Declared ``modules`` are read from each resolved manifest, so modules
        reached only through ``depends_on`` (dependencies) are excluded.
        """
        configs = self._resolved_module_configs or {self.config.name: self.config}
        composed = {self.config.name}
        pending = [self.config.name]
        while pending:
            config = configs.get(pending.pop())
            if config is None or config.source_file is None:
                continue
            declared = KnowledgeBaseConfig.from_yaml_file(config.source_file).modules
            for child in declared:
                if child not in composed:
                    composed.add(child)
                    pending.append(child)
        return frozenset(composed)

    def unresolved_template_validator_references(
        self,
    ) -> tuple[tuple[str, str, str], ...]:
        """Return ``(template, validator_model, name)`` for unresolved names.

        Only published templates are checked: drafts may reference validators
        that are still being authored and report them as preview issues.
        Names resolve only within the loaded package and its dependency closure.
        """
        missing: list[tuple[str, str, str]] = []
        for template_name, template in sorted(self.report_template.items()):
            if self.get_report_template_lifecycle_status(template_name) != "published":
                continue
            for model_name, names in (
                ("examination_validator", template.validators.examination_validators),
                ("findings_validator", template.validators.findings_validators),
                (
                    "classification_validator",
                    template.validators.classification_validators,
                ),
                (
                    "intervention_validator",
                    template.validators.intervention_validators,
                ),
                ("unit_validator", template.validators.unit_validators),
            ):
                defined: Mapping[str, object] = getattr(self, model_name)
                missing.extend(
                    (template_name, model_name, name)
                    for name in names
                    if name not in defined
                )
        return tuple(missing)

    def import_knowledge_base(self, other: "KnowledgeBase") -> None:
        """
        Merge records from another KnowledgeBase into this instance.

        Duplicate model names are rejected before mutation, including identical
        redefinitions. The tags list is merged as a union. Fields listed in
        YAML_IMPORT_SKIP_FIELDS are ignored.

        Parameters:
            other (KnowledgeBase): KnowledgeBase whose records will be merged into this one.

        Raises:
            ValueError: If both knowledge bases define the same model and name.
            AssertionError: If a model field name is not recognised or if the expected model collections are not dicts.
        """
        for model_name in KB_MODEL_NAMES_ORDERED:
            field_name = camel_to_snake(model_name)
            current: dict[str, KB_MODELS] = getattr(self, field_name)
            incoming: dict[str, KB_MODELS] = getattr(other, field_name)
            for key in sorted(current.keys() & incoming.keys()):
                previous, replacement = current[key], incoming[key]
                previous_source = self._definition_location(field_name, key, previous)
                incoming_source = other._definition_location(
                    field_name, key, replacement
                )
                guidance = "Keep one definition in the owning terminology package."
                previous_reporting = previous.kb_module_name in self._reporting_modules
                incoming_reporting = (
                    replacement.kb_module_name in other._reporting_modules
                )
                if (
                    field_name in CLINICAL_CONCEPT_MODELS
                    and previous_reporting != incoming_reporting
                ):
                    owner, source = (
                        (replacement, incoming_source)
                        if previous_reporting
                        else (previous, previous_source)
                    )
                    guidance = (
                        f"Remove the reporting copy and reference '{key}' from "
                        f"module '{owner.kb_module_name}' at {source}."
                    )
                raise ValueError(
                    f"Conflicting '{field_name}' definition '{key}': "
                    f"module '{previous.kb_module_name}' ({previous_source}) and "
                    f"module '{replacement.kb_module_name}' ({incoming_source}). "
                    f"{guidance} Redefinitions are not allowed. See "
                    "docs/guides/dtypes-package-structure.md."
                )
        for field_name in KnowledgeBase.model_fields:
            field_model_name = snake_to_camel(field_name)
            if field_name in YAML_IMPORT_SKIP_FIELDS:
                continue  # skip config

            if field_name == "tags":
                current_tags = set(getattr(self, "tags", []))
                other_tags = set(getattr(other, "tags", []))
                merged_tags = list(current_tags.union(other_tags))
                setattr(self, field_name, merged_tags)
                continue

            if field_name == "report_template_lifecycle_status":
                current_lifecycle = dict(
                    getattr(self, "report_template_lifecycle_status", {})
                )
                other_lifecycle = dict(
                    getattr(other, "report_template_lifecycle_status", {})
                )
                current_lifecycle.update(other_lifecycle)
                setattr(self, field_name, current_lifecycle)
                continue

            if field_model_name not in KB_MODEL_NAMES_ORDERED:
                raise ValueError(f"Unknown model type: {field_model_name}")
            field_model_name = cast(KB_MODEL_NAMES_LITERAL, field_model_name)
            target_model_value = knowledge_base_models_lookup[field_model_name]
            if not isinstance(target_model_value, type) or not issubclass(
                target_model_value, BaseModel
            ):
                raise TypeError(
                    f"Knowledge-base lookup {field_model_name} is not a "
                    "Pydantic model class"
                )
            TargetModel = target_model_value

            current_models = dict(getattr(self, field_name))
            other_models = getattr(other, field_name)
            if not isinstance(other_models, dict):
                raise TypeError(
                    f"Knowledge-base field {field_name!r} must be a dictionary"
                )

            for key, value in other_models.items():
                current_models[key] = (
                    value
                    if isinstance(value, TargetModel)
                    else TargetModel.model_validate(value)
                )

            setattr(self, field_name, current_models)
        self._definition_locations.update(other._definition_locations)
        self._reporting_modules.update(other._reporting_modules)

    def export_knowledge_base(
        self, export_dir: Path, filename: str = "knowledge_base"
    ) -> None:
        """
        Write the knowledge base's ddict representation to a YAML file named "{filename}.yaml" in the given directory.

        Parameters:
            export_dir (Path): Destination directory for the exported YAML file.
            filename (str): Base filename (without extension) to use for the YAML file; defaults to "knowledge_base".
        """
        dump = self.ddict
        export_path = export_dir / f"{filename}.yaml"

        with open(export_path, "w", encoding="utf-8") as f:
            yaml.dump(dump, f)

    def kb_entries_by_module_name(
        self,
    ) -> dict[str, list[tuple["KB_MODEL_NAMES_LITERAL", "KB_MODELS"]]]:
        """
        Group knowledge-base entries by their declaring module name.

        Iterates over the canonical model export order and collects each model instance under the module name found on the instance (`kb_module_name`). Each list contains tuples of the model name (one of `KB_MODEL_NAMES_LITERAL`) and the model instance, preserving the order of models visited.

        Returns:
            Dict[str, List[Tuple[KB_MODEL_NAMES_LITERAL, KB_MODELS]]]: Mapping from module name to a list of (model-name, model-instance) tuples.

        Raises:
            KeyError: If an entry references a module name not present in the knowledge base config.
        """
        export_attrs = KB_MODEL_NAMES_ORDERED
        cfg = self.config
        module_names = cfg.modules
        entries_by_module: dict[str, list[tuple[KB_MODEL_NAMES_LITERAL, KB_MODELS]]] = {
            module_name: [] for module_name in module_names
        }

        # entries_by_module[str_unknown_factory()] = []

        for attr in export_attrs:
            field_name = camel_to_snake(attr)
            kb_dict: dict[str, KB_MODELS] = getattr(self, field_name)
            kb_entry_list: list[KB_MODELS] = list(kb_dict.values())
            for entry in kb_entry_list:
                module_name = entry.kb_module_name

                if module_name not in entries_by_module:
                    raise KeyError(
                        f"Module name '{module_name}' not found in knowledge base config."
                    )
                entries_by_module[module_name].append((attr, entry))

        return entries_by_module

    def export_record_lists(self) -> KnowledgeBaseRecordList:
        """Every registered family as a list of ddicts, keyed ``<field>s``.

        Derived from ``KB_MODEL_NAMES_ORDERED`` so a new family needs no change
        here; ``KnowledgeBaseRecordList`` remains the typed contract.
        """
        records: dict[str, list[KB_DDICTS]] = {}
        for model_name in KB_MODEL_NAMES_ORDERED:
            field_name = camel_to_snake(model_name)
            collection: dict[str, KB_MODELS] = getattr(self, field_name)
            records[f"{field_name}s"] = [record.ddict for record in collection.values()]
        return cast(KnowledgeBaseRecordList, records)

    # Compatibility API: implementations live in the focused adapters.

    def export_report_template_preview(self, name: str) -> dict[str, Any]:
        """Delegate to KnowledgeBaseReporting.export_report_template_preview."""
        return KnowledgeBaseReporting(self).export_report_template_preview(name)

    def export_report_template(self, name: str) -> dict[str, Any]:
        """Delegate to KnowledgeBaseReporting.export_report_template."""
        return KnowledgeBaseReporting(self).export_report_template(name)

    def export_report_templates(
        self, *, published_only: bool = True
    ) -> list[dict[str, Any]]:
        """Delegate to KnowledgeBaseReporting.export_report_templates."""
        return KnowledgeBaseReporting(self).export_report_templates(
            published_only=published_only
        )

    def export_core_concepts(self) -> dict[str, Any]:
        """Delegate to KnowledgeBaseInterop.export_core_concepts."""
        return KnowledgeBaseInterop(self).export_core_concepts()

    def export_fhir_terminology(
        self,
        *,
        base_url: str = "https://wg-lux.de/fhir",
        publisher: str = "Working Group Lux",
        bundle: bool = False,
        medical_field: str | None = None,
    ) -> dict[str, Any]:
        """Delegate to KnowledgeBaseInterop.export_fhir_terminology."""
        return KnowledgeBaseInterop(self).export_fhir_terminology(
            base_url=base_url,
            publisher=publisher,
            bundle=bundle,
            medical_field=medical_field,
        )

    @staticmethod
    def import_fhir_terminology(
        payload: Mapping[str, Any] | list[Mapping[str, Any]],
        *,
        module_name: str = "fhir_import",
        language: str | None = None,
    ) -> dict[str, Any]:
        """Delegate to KnowledgeBaseInterop.import_fhir_terminology."""
        return KnowledgeBaseInterop.import_fhir_terminology(
            payload, module_name=module_name, language=language
        )

    @classmethod
    def from_fhir(
        cls,
        payload: Mapping[str, Any] | list[Mapping[str, Any]],
        *,
        module_name: str = "fhir_import",
        version: str | None = None,
        medical_field: str | None = None,
        author: str | None = None,
        language: str | None = None,
        strict: bool = True,
    ) -> Self:
        """Delegate to KnowledgeBaseInterop.from_fhir."""
        return cast(
            Self,
            KnowledgeBaseInterop.from_fhir(
                payload,
                module_name=module_name,
                version=version,
                medical_field=medical_field,
                author=author,
                language=language,
                strict=strict,
            ),
        )

    def reported_findings_from_p_examination(
        self, p_examination: "PExamination"
    ) -> list[dict[str, Any]]:
        """Delegate to KnowledgeBaseReporting.reported_findings_from_p_examination."""
        return KnowledgeBaseReporting(self).reported_findings_from_p_examination(
            p_examination
        )

    def reported_findings_from_ledger(
        self, ledger: "Ledger", patient_examination_uuid: str
    ) -> list[dict[str, Any]]:
        """Delegate to KnowledgeBaseReporting.reported_findings_from_ledger."""
        return KnowledgeBaseReporting(self).reported_findings_from_ledger(
            ledger, patient_examination_uuid
        )

    def assert_examination_admissibility(
        self, p_examination: "PExamination", *, template_name: str | None = None
    ) -> None:
        """Delegate to KnowledgeBaseAdmissibility.assert_examination_admissibility."""
        return KnowledgeBaseAdmissibility(self).assert_examination_admissibility(
            p_examination, template_name=template_name
        )

    def evaluate_report_template_validators(
        self,
        name: str,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
        *,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> ReportTemplateRuntimeValidationResultDataDict:
        """Delegate to KnowledgeBaseReporting.evaluate_report_template_validators."""
        return KnowledgeBaseReporting(self).evaluate_report_template_validators(
            name, p_examination, ledger, patient_examination_uuid, language=language
        )

    def evaluate_findings_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> FindingsValidatorExecutionDataDict:
        """Delegate to KnowledgeBaseReporting.evaluate_findings_validator."""
        return KnowledgeBaseReporting(self).evaluate_findings_validator(
            validator_name,
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
            language=language,
        )

    def evaluate_classification_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> ClassificationValidatorExecutionDataDict:
        """Delegate to KnowledgeBaseReporting.evaluate_classification_validator."""
        return KnowledgeBaseReporting(self).evaluate_classification_validator(
            validator_name,
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
            language=language,
        )

    def evaluate_intervention_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> InterventionValidatorExecutionDataDict:
        """Delegate to KnowledgeBaseReporting.evaluate_intervention_validator."""
        return KnowledgeBaseReporting(self).evaluate_intervention_validator(
            validator_name,
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
            language=language,
        )

    def evaluate_unit_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> UnitValidatorExecutionDataDict:
        """Delegate to KnowledgeBaseReporting.evaluate_unit_validator."""
        return KnowledgeBaseReporting(self).evaluate_unit_validator(
            validator_name,
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
            language=language,
        )

    def evaluate_examination_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> ExaminationValidatorExecutionDataDict:
        """Delegate to KnowledgeBaseReporting.evaluate_examination_validator."""
        return KnowledgeBaseReporting(self).evaluate_examination_validator(
            validator_name,
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
            language=language,
        )

    def export_terminology_validated_fhir_observations(
        self,
        reported_findings: Sequence[Mapping[str, object]],
        *,
        base_url: str = "https://wg-lux.de/fhir",
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> FhirTerminologyValidatedFindingResultDataDict:
        """Delegate to KnowledgeBaseInterop.export_terminology_validated_fhir_observations."""
        return KnowledgeBaseInterop(
            self
        ).export_terminology_validated_fhir_observations(
            reported_findings, base_url=base_url, language=language
        )

    def import_terminology_validated_fhir_observations(
        self,
        observations: Sequence[Mapping[str, object]],
        *,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
        text_extractor: FindingTextExtractor | None = None,
    ) -> FhirTerminologyValidatedFindingResultDataDict:
        """Delegate to KnowledgeBaseInterop.import_terminology_validated_fhir_observations."""
        return KnowledgeBaseInterop(
            self
        ).import_terminology_validated_fhir_observations(
            observations, language=language, text_extractor=text_extractor
        )

    def get_report_template_classification_validators(
        self, name: str
    ) -> dict[str, ClassificationValidator]:
        """Delegate to KnowledgeBaseReporting.get_report_template_classification_validators."""
        return KnowledgeBaseReporting(
            self
        ).get_report_template_classification_validators(name)
