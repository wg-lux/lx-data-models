from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Mapping,
    Sequence,
    Self,
    Tuple,
    TypedDict,
    Union,
    cast,
)

import yaml
from pydantic import Field, PrivateAttr

from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.contracts import kb_to_core_concepts_payload
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base import (
    KB_MODEL_NAMES_LITERAL,
    KB_MODEL_NAMES_ORDERED,
    KB_MODELS,
    knowledge_base_models_lookup,
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
from lx_dtypes.models.knowledge_base.examination.Examination import Examination
from lx_dtypes.models.knowledge_base.examination.ExaminationDataDict import (
    ExaminationDataDict,
)
from lx_dtypes.models.knowledge_base.examination.ExaminationType import ExaminationType
from lx_dtypes.models.knowledge_base.examination.ExaminationTypeDataDict import (
    ExaminationTypeDataDict,
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
from lx_dtypes.models.knowledge_base.report_template.ExaminationValidator import (
    ExaminationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ExaminationValidatorDataDict import (
    ExaminationValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ClassificationValidator import (
    ClassificationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ClassificationValidatorDataDict import (
    ClassificationValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.InterventionValidator import (
    InterventionValidator,
)
from lx_dtypes.models.knowledge_base.report_template.InterventionValidatorDataDict import (
    InterventionValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidator,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidatorDataDict import (
    FindingsValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import ReportFinding
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
    ReportTemplateReadinessSummary,
)
from lx_dtypes.models.knowledge_base.report_template.UnitValidator import UnitValidator
from lx_dtypes.models.knowledge_base.report_template.UnitValidatorDataDict import (
    UnitValidatorDataDict,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRuntime import (
    ClassificationValidatorExecutionDataDict,
    ExaminationValidatorExecutionDataDict,
    FhirTerminologyValidatedFindingResultDataDict,
    FindingsValidatorExecutionDataDict,
    InterventionValidatorExecutionDataDict,
    ReportTemplateRuntimeValidationResultDataDict,
    UnitValidatorExecutionDataDict,
    evaluate_classification_validator_runtime,
    evaluate_findings_validator_runtime,
    evaluate_intervention_validator_runtime,
    evaluate_report_template_validators_runtime,
    evaluate_unit_validator_runtime,
    export_terminology_validated_fhir_observations,
    import_terminology_validated_fhir_observations,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import (
    ReportTemplateClassificationRequirement,
    ReportTemplateFindingRequirement,
)
from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitDataDict import UnitDataDict
from lx_dtypes.models.knowledge_base.unit.UnitType import UnitType
from lx_dtypes.models.knowledge_base.unit.UnitTypeDataDict import UnitTypeDataDict
from lx_dtypes.utils.parser import (
    camel_to_snake,
    parse_shallow_object_with_meta,
    snake_to_camel,
)
from lx_dtypes.utils.report_template_registry import (
    load_report_template_registry,
    registry_path_for_module,
)
from lx_dtypes.models.interface.ReportTemplateCompiler import ReportTemplateCompiler
from lx_dtypes.models.interface.ReportTemplateValidator import ReportTemplateValidator
from lx_dtypes.models.interface.LookupTracker import KnowledgeBaseLookupTracker

if TYPE_CHECKING:
    from lx_dtypes.models.interface.Ledger import Ledger
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


class KnowledgeBaseDDict(AppBaseModelUUIDTagsDataDict):
    config: KnowledgeBaseConfig
    citation: Dict[str, CitationDataDict]
    classification: Dict[str, ClassificationDataDict]
    classification_type: Dict[str, ClassificationTypeDataDict]
    classification_choice: Dict[str, ClassificationChoiceDataDict]
    classification_choice_descriptor: Dict[str, ClassificationChoiceDescriptorDataDict]
    examination: Dict[str, ExaminationDataDict]
    examination_type: Dict[str, ExaminationTypeDataDict]
    finding: Dict[str, FindingDataDict]
    finding_type: Dict[str, FindingTypeDataDict]
    indication: Dict[str, IndicationDataDict]
    indication_type: Dict[str, IndicationTypeDataDict]
    intervention: Dict[str, InterventionDataDict]
    intervention_type: Dict[str, InterventionTypeDataDict]
    unit_type: Dict[str, UnitTypeDataDict]
    unit: Dict[str, UnitDataDict]
    information_source: Dict[str, InformationSourceDataDict]
    information_source_type: Dict[str, InformationSourceTypeDataDict]
    report_template_section: Dict[str, ReportTemplateSectionDataDict]
    report_finding: Dict[str, ReportFindingDataDict]
    classification_validator: Dict[str, ClassificationValidatorDataDict]
    intervention_validator: Dict[str, InterventionValidatorDataDict]
    unit_validator: Dict[str, UnitValidatorDataDict]
    findings_validator: Dict[str, FindingsValidatorDataDict]
    examination_validator: Dict[str, ExaminationValidatorDataDict]
    report_template: Dict[str, ReportTemplateDataDict]
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
    citations: List[CitationDataDict]
    classifications: List[ClassificationDataDict]
    classification_types: List[ClassificationTypeDataDict]
    classification_choices: List[ClassificationChoiceDataDict]
    classification_choice_descriptors: List[ClassificationChoiceDescriptorDataDict]
    examinations: List[ExaminationDataDict]
    examination_types: List[ExaminationTypeDataDict]
    findings: List[FindingDataDict]
    finding_types: List[FindingTypeDataDict]
    indications: List[IndicationDataDict]
    indication_types: List[IndicationTypeDataDict]
    interventions: List[InterventionDataDict]
    intervention_types: List[InterventionTypeDataDict]
    units: List[UnitDataDict]
    unit_types: List[UnitTypeDataDict]
    information_sources: List[InformationSourceDataDict]
    information_source_types: List[InformationSourceTypeDataDict]
    report_template_sections: List[ReportTemplateSectionDataDict]
    report_findings: List[ReportFindingDataDict]
    classification_validators: List[ClassificationValidatorDataDict]
    intervention_validators: List[InterventionValidatorDataDict]
    unit_validators: List[UnitValidatorDataDict]
    findings_validators: List[FindingsValidatorDataDict]
    examination_validators: List[ExaminationValidatorDataDict]
    report_templates: List[ReportTemplateDataDict]


class SemanticAdmissibilityError(ValueError):
    """
    Raised when a structurally valid ledger instance violates KnowledgeBase semantics.
    """


class KnowledgeBase(AppBaseModelUUIDTags):
    config: KnowledgeBaseConfig
    citation: Dict[str, Citation] = Field(default_factory=dict)
    classification: Dict[str, Classification] = Field(default_factory=dict)
    classification_type: Dict[str, ClassificationType] = Field(default_factory=dict)
    classification_choice: Dict[str, ClassificationChoice] = Field(default_factory=dict)
    classification_choice_descriptor: Dict[str, ClassificationChoiceDescriptor] = Field(
        default_factory=dict
    )
    examination: Dict[str, Examination] = Field(default_factory=dict)
    examination_type: Dict[str, ExaminationType] = Field(default_factory=dict)
    finding: Dict[str, Finding] = Field(default_factory=dict)
    finding_type: Dict[str, FindingType] = Field(default_factory=dict)
    indication: Dict[str, Indication] = Field(default_factory=dict)
    indication_type: Dict[str, IndicationType] = Field(default_factory=dict)
    intervention: Dict[str, Intervention] = Field(default_factory=dict)
    intervention_type: Dict[str, InterventionType] = Field(default_factory=dict)
    unit_type: Dict[str, UnitType] = Field(default_factory=dict)
    unit: Dict[str, Unit] = Field(default_factory=dict)
    information_source: Dict[str, InformationSource] = Field(default_factory=dict)
    information_source_type: Dict[str, InformationSourceType] = Field(
        default_factory=dict
    )
    report_template_section: Dict[str, ReportTemplateSection] = Field(
        default_factory=dict
    )
    report_finding: Dict[str, ReportFinding] = Field(default_factory=dict)
    classification_validator: Dict[str, ClassificationValidator] = Field(
        default_factory=dict
    )
    intervention_validator: Dict[str, InterventionValidator] = Field(
        default_factory=dict
    )
    unit_validator: Dict[str, UnitValidator] = Field(default_factory=dict)
    findings_validator: Dict[str, FindingsValidator] = Field(default_factory=dict)
    examination_validator: Dict[str, ExaminationValidator] = Field(default_factory=dict)
    report_template: Dict[str, ReportTemplate] = Field(default_factory=dict)
    report_template_lifecycle_status: Dict[
        str, ReportTemplateLifecycleStatusLiteral
    ] = Field(default_factory=dict, exclude=True)
    _lookup_tracker: KnowledgeBaseLookupTracker = PrivateAttr(
        default_factory=KnowledgeBaseLookupTracker
    )

    def _lookup_required(
        self,
        *,
        collection_name: str,
        key: str,
        source: str = "knowledge_base",
    ) -> Any:
        collection = cast(Dict[str, Any], getattr(self, collection_name))
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
        collection = cast(Dict[str, Any], getattr(self, collection_name))
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

    def get_lookup_tracker_summary(self) -> Dict[str, Any]:
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
    ) -> Dict[str, Any]:
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

    def published_report_template_names(self) -> List[str]:
        return [
            template_name
            for template_name in self.report_template.keys()
            if self.get_report_template_lifecycle_status(template_name) == "published"
        ]

    def export_report_template_preview(self, name: str) -> Dict[str, Any]:
        validator = ReportTemplateValidator(
            kb=self, compiler=ReportTemplateCompiler(kb=self)
        )
        validated_and_compiled = validator.validate_and_compile(name, mode="preview")
        return cast(Dict[str, Any], validated_and_compiled["template"])

    def export_report_template(self, name: str) -> Dict[str, Any]:
        validator = ReportTemplateValidator(
            kb=self, compiler=ReportTemplateCompiler(kb=self)
        )
        validated_and_compiled = validator.validate_and_compile(name, mode="production")
        summary = cast(
            ReportTemplateReadinessSummary, validated_and_compiled["summary"]
        )
        if summary.lifecycle_status != "published":
            raise KeyError(
                f"Report template '{name}' is not published for production export."
            )
        if not summary.can_publish:
            raise KeyError(
                f"Report template '{name}' is not production-ready for export."
            )
        return cast(Dict[str, Any], validated_and_compiled["template"])

    def export_report_templates(
        self, *, published_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Export report templates as frontend-friendly dicts.
        """
        template_names = (
            self.published_report_template_names()
            if published_only
            else list(self.report_template.keys())
        )
        exporter = (
            self.export_report_template
            if published_only
            else self.export_report_template_preview
        )
        return [exporter(template_name) for template_name in template_names]

    def export_core_concepts(self) -> Dict[str, Any]:
        """
        Export canonical core concept payloads for frontend consumption.
        """
        payload = kb_to_core_concepts_payload(self)
        return payload.model_dump(mode="json")

    def export_fhir_terminology(
        self,
        *,
        base_url: str = "https://wg-lux.de/fhir",
        publisher: str = "Working Group Lux",
        bundle: bool = False,
        medical_field: str | None = None,
    ) -> Dict[str, Any]:
        """
        Export core KB terminology as FHIR CodeSystem and ValueSet resources.
        """
        from lx_dtypes.models.knowledge_base.fhir import (
            export_fhir_terminology,
            export_fhir_terminology_bundle,
        )

        if bundle:
            return export_fhir_terminology_bundle(
                self,
                base_url=base_url,
                publisher=publisher,
                medical_field=medical_field,
            )
        return export_fhir_terminology(
            self,
            base_url=base_url,
            publisher=publisher,
            medical_field=medical_field,
        )

    @staticmethod
    def import_fhir_terminology(
        payload: Mapping[str, Any] | List[Mapping[str, Any]],
        *,
        module_name: str = "fhir_import",
    ) -> Dict[str, Any]:
        """
        Import FHIR CodeSystem resources into KB storage-compatible concepts.
        """
        from lx_dtypes.models.knowledge_base.fhir import import_fhir_terminology

        return import_fhir_terminology(payload, module_name=module_name)

    def reported_findings_from_p_examination(
        self, p_examination: "PExamination"
    ) -> List[Dict[str, Any]]:
        reported_findings: List[Dict[str, Any]] = []

        for p_finding in p_examination.patient_findings:
            classifications_payload: List[Dict[str, Any]] = []
            for classifications in p_finding.patient_finding_classifications:
                for choice in classifications.patient_finding_classification_choices:
                    base_payload: Dict[str, Any] = {
                        "classification": choice.classification,
                        "classification_choice": choice.classification_choice,
                        "value": choice.classification_choice,
                    }
                    classifications_payload.append(base_payload)

                    for (
                        descriptor
                    ) in choice.patient_finding_classification_choice_descriptors:
                        descriptor_payload: Dict[str, Any] = {
                            "classification": choice.classification,
                            "value": descriptor.descriptor_value,
                        }
                        kb_descriptor = self._lookup_optional(
                            collection_name="classification_choice_descriptor",
                            key=descriptor.classification_choice_descriptor,
                            source="reported_findings_from_p_examination",
                        )
                        if kb_descriptor is not None and kb_descriptor.unit:
                            descriptor_payload["unit"] = kb_descriptor.unit
                        classifications_payload.append(descriptor_payload)

            interventions_payload = [
                {"intervention": intervention.intervention}
                for interventions in p_finding.patient_finding_interventions
                for intervention in interventions.patient_finding_interventions
            ]

            reported_findings.append(
                {
                    "finding": p_finding.finding,
                    "classifications": classifications_payload,
                    "interventions": interventions_payload,
                }
            )

        return reported_findings

    def reported_findings_from_ledger(
        self, ledger: "Ledger", patient_examination_uuid: str
    ) -> List[Dict[str, Any]]:
        p_examination = ledger.patient_examinations[patient_examination_uuid]
        return self.reported_findings_from_p_examination(p_examination)

    @staticmethod
    def _names_as_list(value: str | List[str]) -> List[str]:
        if isinstance(value, list):
            return [item for item in value if item]
        if value:
            return [value]
        return []

    def assert_examination_admissibility(
        self,
        p_examination: "PExamination",
        *,
        template_name: str | None = None,
    ) -> None:
        def template_requirements_by_finding(
            resolved_template_name: str,
        ) -> Dict[str, ReportTemplateFindingRequirement]:
            def ensure_requirement(finding_name: str) -> None:
                requirements.setdefault(
                    finding_name,
                    ReportTemplateFindingRequirement(finding=finding_name),
                )

            def ensure_classification_requirement(
                finding_name: str,
                classification_name: str,
            ) -> None:
                ensure_requirement(finding_name)
                requirement = requirements[finding_name]
                if any(
                    existing.classification == classification_name
                    for existing in requirement.classifications
                ):
                    return
                requirement.classifications.append(
                    ReportTemplateClassificationRequirement(
                        classification=classification_name
                    )
                )

            def collect_from_examination_validator(validator_name: str) -> None:
                if validator_name in visited_exam_validators:
                    return
                visited_exam_validators.add(validator_name)
                examination_validator = self._lookup_optional(
                    collection_name="examination_validator",
                    key=validator_name,
                    source="assert_examination_admissibility",
                )
                if examination_validator is None:
                    return
                for finding_validator_name in self._names_as_list(
                    examination_validator.finding_validators
                ):
                    finding_validator = self._lookup_optional(
                        collection_name="findings_validator",
                        key=finding_validator_name,
                        source="assert_examination_admissibility",
                    )
                    if finding_validator is not None:
                        ensure_requirement(finding_validator.finding)
                        if finding_validator.query.condition is not None:
                            for (
                                requirement_reference
                            ) in finding_validator.query.condition.then_requires:
                                if requirement_reference.kind == "classification":
                                    ensure_classification_requirement(
                                        finding_validator.finding,
                                        requirement_reference.classification
                                        or requirement_reference.name,
                                    )
                for nested_exam_validator_name in self._names_as_list(
                    examination_validator.examination_validators
                ):
                    collect_from_examination_validator(nested_exam_validator_name)

            template = self.get_report_template(resolved_template_name)
            requirements: Dict[str, ReportTemplateFindingRequirement] = {}
            visited_exam_validators: set[str] = set()
            for section_name in template.report_sections:
                section = self._lookup_optional(
                    collection_name="report_template_section",
                    key=section_name,
                    source="assert_examination_admissibility",
                )
                if section is None:
                    continue
                for finding_ref in section.findings:
                    if isinstance(finding_ref, str):
                        report_finding = self._lookup_optional(
                            collection_name="report_finding",
                            key=finding_ref,
                            source="assert_examination_admissibility",
                        )
                        if report_finding is None:
                            continue
                        requirement = report_finding.as_requirement()
                    else:
                        requirement = finding_ref
                    requirements[requirement.finding] = requirement
            for findings_validator_name in self._names_as_list(
                template.validators.findings_validators
            ):
                finding_validator = self._lookup_optional(
                    collection_name="findings_validator",
                    key=findings_validator_name,
                    source="assert_examination_admissibility",
                )
                if finding_validator is not None:
                    ensure_requirement(finding_validator.finding)
                    if finding_validator.query.condition is not None:
                        for (
                            requirement_reference
                        ) in finding_validator.query.condition.then_requires:
                            if requirement_reference.kind == "classification":
                                ensure_classification_requirement(
                                    finding_validator.finding,
                                    requirement_reference.classification
                                    or requirement_reference.name,
                                )
            for classification_validator_name in self._names_as_list(
                template.validators.classification_validators
            ):
                classification_validator = self._lookup_optional(
                    collection_name="classification_validator",
                    key=classification_validator_name,
                    source="assert_examination_admissibility",
                )
                if classification_validator is not None:
                    ensure_classification_requirement(
                        classification_validator.finding,
                        classification_validator.classification,
                    )
            for examination_validator_name in self._names_as_list(
                template.validators.examination_validators
            ):
                collect_from_examination_validator(examination_validator_name)
            return requirements

        requirements_by_finding: Dict[str, ReportTemplateFindingRequirement]
        if template_name is not None:
            template = self.get_report_template(template_name)
            if template.examination != p_examination.examination:
                raise SemanticAdmissibilityError(
                    "PExamination examination "
                    f"'{p_examination.examination}' does not match report template "
                    f"'{template_name}' examination '{template.examination}'."
                )
            requirements_by_finding = template_requirements_by_finding(template_name)
        else:
            requirements_by_finding = {}
            examination = self._lookup_optional(
                collection_name="examination",
                key=p_examination.examination,
                source="assert_examination_admissibility",
            )
            if examination is not None:
                for finding_name in self._names_as_list(examination.findings):
                    requirements_by_finding.setdefault(
                        finding_name,
                        ReportTemplateFindingRequirement(finding=finding_name),
                    )
            for report_template in self.report_template.values():
                if report_template.examination != p_examination.examination:
                    continue
                requirements_by_finding.update(
                    template_requirements_by_finding(report_template.name)
                )
            if p_examination.examination not in self.examination and not any(
                report_template.examination == p_examination.examination
                for report_template in self.report_template.values()
            ):
                raise SemanticAdmissibilityError(
                    f"Unknown examination '{p_examination.examination}'."
                )

        allowed_findings = set(requirements_by_finding.keys())
        examination = self.examination.get(p_examination.examination)
        allowed_indications = (
            set(self._names_as_list(examination.indications))
            if examination is not None
            else set()
        )
        for p_finding in p_examination.patient_findings:
            kb_finding = self._lookup_optional(
                collection_name="finding",
                key=p_finding.finding,
                source="assert_examination_admissibility",
            )
            requirement = requirements_by_finding.get(p_finding.finding)
            if allowed_findings and p_finding.finding not in allowed_findings:
                raise SemanticAdmissibilityError(
                    f"Finding '{p_finding.finding}' is not permitted for examination "
                    f"'{p_examination.examination}'."
                )
            if kb_finding is None and requirement is None:
                raise SemanticAdmissibilityError(
                    f"Unknown finding '{p_finding.finding}'."
                )

            allowed_classifications = (
                set(self._names_as_list(kb_finding.classifications))
                if kb_finding is not None
                else set()
            )
            if requirement is not None:
                allowed_classifications.update(
                    classification_requirement.classification
                    for classification_requirement in requirement.classifications
                )
            allowed_interventions = (
                set(self._names_as_list(kb_finding.interventions))
                if kb_finding is not None
                else set()
            )

            for classifications in p_finding.patient_finding_classifications:
                for choice in classifications.patient_finding_classification_choices:
                    kb_classification = self._lookup_optional(
                        collection_name="classification",
                        key=choice.classification,
                        source="assert_examination_admissibility",
                    )
                    if (
                        kb_classification is None
                        and choice.classification not in allowed_classifications
                    ):
                        raise SemanticAdmissibilityError(
                            f"Unknown classification '{choice.classification}'."
                        )
                    if choice.classification not in allowed_classifications:
                        raise SemanticAdmissibilityError(
                            f"Classification '{choice.classification}' is not "
                            f"permitted for finding '{p_finding.finding}'."
                        )

                    allowed_choices = (
                        set(
                            self._names_as_list(
                                kb_classification.classification_choices
                            )
                        )
                        if kb_classification is not None
                        else set()
                    )
                    kb_choice = self._lookup_optional(
                        collection_name="classification_choice",
                        key=choice.classification_choice,
                        source="assert_examination_admissibility",
                    )
                    if kb_choice is None and allowed_choices:
                        raise SemanticAdmissibilityError(
                            f"Unknown classification choice "
                            f"'{choice.classification_choice}'."
                        )
                    if (
                        allowed_choices
                        and choice.classification_choice not in allowed_choices
                    ):
                        raise SemanticAdmissibilityError(
                            f"Classification choice '{choice.classification_choice}' is "
                            f"not permitted for classification '{choice.classification}'."
                        )

                    allowed_descriptors = (
                        set(
                            self._names_as_list(
                                kb_choice.classification_choice_descriptors
                            )
                        )
                        if kb_choice is not None
                        else set()
                    )
                    for (
                        descriptor
                    ) in choice.patient_finding_classification_choice_descriptors:
                        if (
                            descriptor.classification_choice_descriptor
                            not in self.classification_choice_descriptor
                            and allowed_descriptors
                        ):
                            raise SemanticAdmissibilityError(
                                "Unknown classification choice descriptor "
                                f"'{descriptor.classification_choice_descriptor}'."
                            )
                        if (
                            allowed_descriptors
                            and descriptor.classification_choice_descriptor
                            not in allowed_descriptors
                        ):
                            raise SemanticAdmissibilityError(
                                "Classification choice descriptor "
                                f"'{descriptor.classification_choice_descriptor}' is "
                                "not permitted for classification choice "
                                f"'{choice.classification_choice}'."
                            )

            for interventions in p_finding.patient_finding_interventions:
                for intervention in interventions.patient_finding_interventions:
                    if intervention.intervention not in self.intervention:
                        raise SemanticAdmissibilityError(
                            f"Unknown intervention '{intervention.intervention}'."
                        )
                    if intervention.intervention not in allowed_interventions:
                        raise SemanticAdmissibilityError(
                            f"Intervention '{intervention.intervention}' is not "
                            f"permitted for finding '{p_finding.finding}'."
                        )

        for p_indication in p_examination.patient_indications:
            kb_indication = self.indication.get(p_indication.indication)
            if kb_indication is None:
                raise SemanticAdmissibilityError(
                    f"Unknown indication '{p_indication.indication}'."
                )
            if (
                allowed_indications
                and p_indication.indication not in allowed_indications
            ):
                raise SemanticAdmissibilityError(
                    f"Indication '{p_indication.indication}' is not permitted for "
                    f"examination '{p_examination.examination}'."
                )

            allowed_classifications = set(
                self._names_as_list(kb_indication.classifications)
            )
            for (
                p_indication_classification
            ) in p_indication.patient_indication_classifications:
                kb_classification = self.classification.get(
                    p_indication_classification.classification
                )
                if (
                    kb_classification is None
                    and p_indication_classification.classification
                    not in allowed_classifications
                ):
                    raise SemanticAdmissibilityError(
                        "Unknown indication classification "
                        f"'{p_indication_classification.classification}'."
                    )
                if (
                    p_indication_classification.classification
                    not in allowed_classifications
                ):
                    raise SemanticAdmissibilityError(
                        "Classification "
                        f"'{p_indication_classification.classification}' is not "
                        f"permitted for indication '{p_indication.indication}'."
                    )

                allowed_choices = (
                    set(self._names_as_list(kb_classification.classification_choices))
                    if kb_classification is not None
                    else set()
                )
                kb_choice = self.classification_choice.get(
                    p_indication_classification.classification_choice
                )
                if kb_choice is None and allowed_choices:
                    raise SemanticAdmissibilityError(
                        "Unknown indication classification choice "
                        f"'{p_indication_classification.classification_choice}'."
                    )
                if (
                    allowed_choices
                    and p_indication_classification.classification_choice
                    not in allowed_choices
                ):
                    raise SemanticAdmissibilityError(
                        "Classification choice "
                        f"'{p_indication_classification.classification_choice}' is "
                        "not permitted for classification "
                        f"'{p_indication_classification.classification}'."
                    )

                allowed_descriptors = (
                    set(
                        self._names_as_list(kb_choice.classification_choice_descriptors)
                    )
                    if kb_choice is not None
                    else set()
                )
                for indication_descriptor in p_indication_classification.patient_indication_classification_descriptors:
                    if (
                        indication_descriptor.classification_choice_descriptor
                        not in self.classification_choice_descriptor
                        and allowed_descriptors
                    ):
                        raise SemanticAdmissibilityError(
                            "Unknown indication classification choice descriptor "
                            f"'{indication_descriptor.classification_choice_descriptor}'."
                        )
                    if (
                        allowed_descriptors
                        and indication_descriptor.classification_choice_descriptor
                        not in allowed_descriptors
                    ):
                        raise SemanticAdmissibilityError(
                            "Classification choice descriptor "
                            f"'{indication_descriptor.classification_choice_descriptor}' is not "
                            "permitted for classification choice "
                            f"'{p_indication_classification.classification_choice}'."
                        )

    def _normalized_runtime_findings_for_validation(
        self,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
    ) -> List[Dict[str, Any]]:
        if p_examination is not None:
            return self.reported_findings_from_p_examination(p_examination)
        if ledger is not None and patient_examination_uuid is not None:
            return self.reported_findings_from_ledger(ledger, patient_examination_uuid)
        raise ValueError(
            "Validation requires typed patient state via `p_examination` or "
            "`ledger` with `patient_examination_uuid`."
        )

    def evaluate_report_template_validators(
        self,
        name: str,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
    ) -> ReportTemplateRuntimeValidationResultDataDict:
        """
        Execute report-template validators against typed ledger state.

        Parameters:
            name (str): The report template name.
            p_examination (PExamination | None): Typed ledger examination instance.
            ledger (Ledger | None): Typed ledger instance.
            patient_examination_uuid (str | None): UUID used with `ledger`.

        Returns:
            ReportTemplateRuntimeValidationResultDataDict: Runtime validator execution result.
        """
        if p_examination is not None:
            self.assert_examination_admissibility(
                p_examination,
                template_name=name,
            )
        elif ledger is not None and patient_examination_uuid is not None:
            self.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid],
                template_name=name,
            )
        template = self.get_report_template(name)
        classification_validators = self.get_report_template_classification_validators(
            name
        )
        classification_validator_names = list(
            template.validators.classification_validators
        )
        classification_validator_names.extend(
            [
                validator_name
                for validator_name in classification_validators.keys()
                if validator_name not in classification_validator_names
            ]
        )
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        return evaluate_report_template_validators_runtime(
            template,
            classification_validators=classification_validators,
            classification_validator_names=classification_validator_names,
            intervention_validators=self.intervention_validator,
            unit_validators=self.unit_validator,
            findings_validators=self.findings_validator,
            examination_validators=self.examination_validator,
            classifications=self.classification,
            classification_choices=self.classification_choice,
            classification_choice_descriptors=self.classification_choice_descriptor,
            interventions=self.intervention,
            units=self.unit,
            reported_findings=normalized_reported_findings,
        )

    def evaluate_findings_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
    ) -> FindingsValidatorExecutionDataDict:
        if p_examination is not None:
            self.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid]
            )
        validator = self.findings_validator[validator_name]
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        return evaluate_findings_validator_runtime(
            validator,
            reported_findings=normalized_reported_findings,
        )

    def evaluate_classification_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
    ) -> ClassificationValidatorExecutionDataDict:
        if p_examination is not None:
            self.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid]
            )
        validator = self.classification_validator[validator_name]
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        return evaluate_classification_validator_runtime(
            validator,
            classifications=self.classification,
            classification_choices=self.classification_choice,
            classification_choice_descriptors=self.classification_choice_descriptor,
            reported_findings=normalized_reported_findings,
        )

    def evaluate_intervention_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
    ) -> InterventionValidatorExecutionDataDict:
        if p_examination is not None:
            self.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid]
            )
        validator = self.intervention_validator[validator_name]
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        return evaluate_intervention_validator_runtime(
            validator,
            interventions=self.intervention,
            reported_findings=normalized_reported_findings,
        )

    def evaluate_unit_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
    ) -> UnitValidatorExecutionDataDict:
        if p_examination is not None:
            self.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid]
            )
        validator = self.unit_validator[validator_name]
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        return evaluate_unit_validator_runtime(
            validator,
            units=self.unit,
            reported_findings=normalized_reported_findings,
        )

    def evaluate_examination_validator(
        self,
        validator_name: str,
        *,
        p_examination: "PExamination | None" = None,
        ledger: "Ledger | None" = None,
        patient_examination_uuid: str | None = None,
    ) -> ExaminationValidatorExecutionDataDict:
        if p_examination is not None:
            self.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid]
            )
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        template = ReportTemplate.model_validate(
            {
                "name": f"single_validator__{validator_name}",
                "examination": "runtime_validation",
                "report_sections": [],
                "validators": {
                    "classification_validators": [],
                    "findings_validators": [],
                    "intervention_validators": [],
                    "examination_validators": [validator_name],
                    "unit_validators": [],
                },
            }
        )
        result = evaluate_report_template_validators_runtime(
            template,
            classification_validators=self.classification_validator,
            classification_validator_names=[],
            intervention_validators=self.intervention_validator,
            unit_validators=self.unit_validator,
            findings_validators=self.findings_validator,
            examination_validators=self.examination_validator,
            classifications=self.classification,
            classification_choices=self.classification_choice,
            classification_choice_descriptors=self.classification_choice_descriptor,
            interventions=self.intervention,
            units=self.unit,
            reported_findings=normalized_reported_findings,
        )
        return result["examination_validators"][0]

    def export_terminology_validated_fhir_observations(
        self,
        reported_findings: Sequence[Mapping[str, object]],
        *,
        base_url: str = "https://wg-lux.de/fhir",
    ) -> FhirTerminologyValidatedFindingResultDataDict:
        return export_terminology_validated_fhir_observations(
            reported_findings,
            findings=self.finding,
            classifications=self.classification,
            classification_choices=self.classification_choice,
            units=self.unit,
            base_url=base_url,
        )

    def import_terminology_validated_fhir_observations(
        self,
        observations: Sequence[Mapping[str, object]],
    ) -> FhirTerminologyValidatedFindingResultDataDict:
        return import_terminology_validated_fhir_observations(
            observations,
            findings=self.finding,
            classifications=self.classification,
            classification_choices=self.classification_choice,
            units=self.unit,
        )

    def get_report_template_classification_validators(
        self, name: str
    ) -> Dict[str, ClassificationValidator]:
        template = self.get_report_template(name)

        validators_by_name: Dict[str, ClassificationValidator] = {}
        explicit_keys: set[tuple[str, str]] = set()
        for validator_name in template.validators.classification_validators:
            validator = self._lookup_optional(
                collection_name="classification_validator",
                key=validator_name,
                source="get_report_template_classification_validators",
            )
            if validator is None:
                continue
            validators_by_name[validator_name] = validator
            explicit_keys.add((validator.finding, validator.classification))

        for section_name in template.report_sections:
            section = self._lookup_optional(
                collection_name="report_template_section",
                key=section_name,
                source="get_report_template_classification_validators",
            )
            if section is None:
                continue
            for finding_ref in section.findings:
                if isinstance(finding_ref, str):
                    report_finding = self._lookup_optional(
                        collection_name="report_finding",
                        key=finding_ref,
                        source="get_report_template_classification_validators",
                    )
                    if report_finding is None:
                        continue
                    finding_requirement = report_finding.as_requirement()
                else:
                    finding_requirement = finding_ref

                for classification_req in finding_requirement.classifications:
                    if not classification_req.required:
                        continue
                    key = (
                        finding_requirement.finding,
                        classification_req.classification,
                    )
                    if key in explicit_keys:
                        continue

                    validator_name = (
                        "implicit_classification_validator__"
                        f"{template.name}__{finding_requirement.finding}__"
                        f"{classification_req.classification}"
                    )
                    validators_by_name[validator_name] = (
                        ClassificationValidator.model_validate(
                            {
                                "name": validator_name,
                                "finding": finding_requirement.finding,
                                "classification": classification_req.classification,
                                "operator": "exists",
                                "precedence": "required",
                                "query": {
                                    "finding": finding_requirement.finding,
                                    "classification": classification_req.classification,
                                    "operator": "exists",
                                },
                            }
                        )
                    )

        return validators_by_name

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
    def create_from_config(cls, config: "KnowledgeBaseConfig") -> "KnowledgeBase":
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
        kb_source_dict: Dict[str, Union["KnowledgeBaseConfig", Path]] = {
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
        seen_records: Dict[Tuple[str, str], Tuple[Path, int, int]] = {}
        data = config.data
        submodule_files = data.get_files_with_suffix(".yaml")
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
                model_dict: Dict[str, KB_MODELS] = getattr(kb, model_name)
                model_dict[object_name] = parsed_object

                # set the updated dict back to the kb
                setattr(kb, model_name, model_dict)
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

    def import_knowledge_base(self, other: "KnowledgeBase") -> None:
        """
        Merge records from another KnowledgeBase into this instance.

        Merges each model collection from `other` into `self` by adding entries from `other` and replacing any existing entries with the same key. The `tags` list is merged as the union of both instances' tags. Fields listed in YAML_IMPORT_SKIP_FIELDS are ignored. Values from `other` will be validated or converted into the target model type when necessary.

        Parameters:
            other (KnowledgeBase): KnowledgeBase whose records will be merged into this one.

        Raises:
            AssertionError: If a model field name is not recognised or if the expected model collections are not dicts.
        """
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

            assert field_model_name in KB_MODEL_NAMES_ORDERED, (
                f"Unknown model type: {field_model_name}"
            )
            field_model_name = cast(KB_MODEL_NAMES_LITERAL, field_model_name)
            TargetModel: type[KB_MODELS] = knowledge_base_models_lookup[
                field_model_name
            ]

            current_models = dict(getattr(self, field_name))
            other_models = getattr(other, field_name)
            assert isinstance(current_models, dict)
            assert isinstance(other_models, dict)

            for key, value in other_models.items():
                if key in current_models:
                    pass  # or raise warning?
                current_models[key] = (
                    value
                    if isinstance(value, TargetModel)
                    else TargetModel.model_validate(value)
                )

            setattr(self, field_name, current_models)

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
    ) -> Dict[str, List[Tuple["KB_MODEL_NAMES_LITERAL", "KB_MODELS"]]]:
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
        entries_by_module: Dict[
            str, List[Tuple["KB_MODEL_NAMES_LITERAL", "KB_MODELS"]]
        ] = {module_name: [] for module_name in module_names}

        # entries_by_module[str_unknown_factory()] = []

        for attr in export_attrs:
            field_name = camel_to_snake(attr)
            kb_dict: Dict[str, "KB_MODELS"] = getattr(self, field_name)
            kb_entry_list: List["KB_MODELS"] = list(kb_dict.values())
            assert isinstance(kb_entry_list, list)
            for entry in kb_entry_list:
                module_name = entry.kb_module_name

                if module_name not in entries_by_module:
                    raise KeyError(
                        f"Module name '{module_name}' not found in knowledge base config."
                    )
                entries_by_module[module_name].append((attr, entry))

        return entries_by_module

    def export_record_lists(self) -> KnowledgeBaseRecordList:
        """
        Collects each knowledge-base model into lists of their ddict (data-dictionary) representations and returns them grouped in a KnowledgeBaseRecordList.
        """
        return KnowledgeBaseRecordList(
            citations=[record.ddict for record in self.citation.values()],
            classifications=[record.ddict for record in self.classification.values()],
            classification_types=[
                record.ddict for record in self.classification_type.values()
            ],
            classification_choices=[
                record.ddict for record in self.classification_choice.values()
            ],
            classification_choice_descriptors=[
                record.ddict
                for record in self.classification_choice_descriptor.values()
            ],
            examinations=[record.ddict for record in self.examination.values()],
            examination_types=[
                record.ddict for record in self.examination_type.values()
            ],
            findings=[record.ddict for record in self.finding.values()],
            finding_types=[record.ddict for record in self.finding_type.values()],
            indications=[record.ddict for record in self.indication.values()],
            indication_types=[record.ddict for record in self.indication_type.values()],
            interventions=[record.ddict for record in self.intervention.values()],
            intervention_types=[
                record.ddict for record in self.intervention_type.values()
            ],
            units=[record.ddict for record in self.unit.values()],
            unit_types=[record.ddict for record in self.unit_type.values()],
            information_sources=[
                record.ddict for record in self.information_source.values()
            ],
            information_source_types=[
                record.ddict for record in self.information_source_type.values()
            ],
            report_template_sections=[
                record.ddict for record in self.report_template_section.values()
            ],
            report_findings=[record.ddict for record in self.report_finding.values()],
            classification_validators=[
                record.ddict for record in self.classification_validator.values()
            ],
            intervention_validators=[
                record.ddict for record in self.intervention_validator.values()
            ],
            unit_validators=[record.ddict for record in self.unit_validator.values()],
            findings_validators=[
                record.ddict for record in self.findings_validator.values()
            ],
            examination_validators=[
                record.ddict for record in self.examination_validator.values()
            ],
            report_templates=[record.ddict for record in self.report_template.values()],
        )
