"""Report compilation, ledger projection and runtime validation using a knowledge base."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from lx_dtypes.language import DEFAULT_LANGUAGE
from lx_dtypes.models.interface.ReportTemplateCompiler import ReportTemplateCompiler
from lx_dtypes.models.interface.ReportTemplateValidator import ReportTemplateValidator
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)
from lx_dtypes.models.knowledge_base.report_template.TemplateReadiness import (
    ReportTemplateReadinessSummary,
)
from lx_dtypes.models.knowledge_base.validators.ClassificationValidator import (
    ClassificationValidator,
)
from lx_dtypes.models.knowledge_base.validators.RuntimeIssues import (
    RuntimeValidationLanguage,
    _runtime_display_names,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRuntime import (
    evaluate_classification_validator_runtime,
    evaluate_findings_validator_runtime,
    evaluate_intervention_validator_runtime,
    evaluate_report_template_validators_runtime,
    evaluate_unit_validator_runtime,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRuntimeDataDict import (
    ClassificationValidatorExecutionDataDict,
    ExaminationValidatorExecutionDataDict,
    FindingsValidatorExecutionDataDict,
    InterventionValidatorExecutionDataDict,
    ReportTemplateRuntimeValidationResultDataDict,
    UnitValidatorExecutionDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
    from lx_dtypes.models.interface.Ledger import Ledger
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


class KnowledgeBaseReporting:
    """Report compilation, ledger projection and runtime validation using a knowledge base."""

    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    def _validation_display_names(
        self, language: RuntimeValidationLanguage
    ) -> dict[str, str]:
        return _runtime_display_names(
            language,
            self.kb.finding.values(),
            self.kb.classification.values(),
            self.kb.classification_choice.values(),
            self.kb.intervention.values(),
            self.kb.unit.values(),
            self.kb.findings_validator.values(),
            self.kb.classification_validator.values(),
            self.kb.intervention_validator.values(),
            self.kb.unit_validator.values(),
            self.kb.examination_validator.values(),
        )

    def export_report_template_preview(self, name: str) -> dict[str, Any]:
        validator = ReportTemplateValidator(
            kb=self.kb, compiler=ReportTemplateCompiler(kb=self.kb)
        )
        validated_and_compiled = validator.validate_and_compile(name, mode="preview")
        return cast(dict[str, Any], validated_and_compiled["template"])

    def export_report_template(self, name: str) -> dict[str, Any]:
        validator = ReportTemplateValidator(
            kb=self.kb, compiler=ReportTemplateCompiler(kb=self.kb)
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
        return cast(dict[str, Any], validated_and_compiled["template"])

    def export_report_templates(
        self, *, published_only: bool = True
    ) -> list[dict[str, Any]]:
        """
        Export report templates as frontend-friendly dicts.
        """
        template_names = (
            self.kb.published_report_template_names()
            if published_only
            else list(self.kb.report_template.keys())
        )
        exporter = (
            self.kb.export_report_template
            if published_only
            else self.kb.export_report_template_preview
        )
        return [exporter(template_name) for template_name in template_names]

    def reported_findings_from_p_examination(
        self, p_examination: PExamination
    ) -> list[dict[str, Any]]:
        reported_findings: list[dict[str, Any]] = []

        for p_finding in p_examination.patient_findings:
            classifications_payload: list[dict[str, Any]] = []
            for classifications in p_finding.patient_finding_classifications:
                for choice in classifications.patient_finding_classification_choices:
                    base_payload: dict[str, Any] = {
                        "classification": choice.classification,
                        "classification_choice": choice.classification_choice,
                        "value": choice.classification_choice,
                    }
                    classifications_payload.append(base_payload)

                    for (
                        descriptor
                    ) in choice.patient_finding_classification_choice_descriptors:
                        descriptor_payload: dict[str, Any] = {
                            "classification": choice.classification,
                            "value": descriptor.descriptor_value,
                        }
                        kb_descriptor = self.kb._lookup_optional(
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
        self, ledger: Ledger, patient_examination_uuid: str
    ) -> list[dict[str, Any]]:
        p_examination = ledger.patient_examinations[patient_examination_uuid]
        return self.kb.reported_findings_from_p_examination(p_examination)

    def _normalized_runtime_findings_for_validation(
        self,
        *,
        p_examination: PExamination | None = None,
        ledger: Ledger | None = None,
        patient_examination_uuid: str | None = None,
    ) -> list[dict[str, Any]]:
        if p_examination is not None:
            return self.kb.reported_findings_from_p_examination(p_examination)
        if ledger is not None and patient_examination_uuid is not None:
            return self.kb.reported_findings_from_ledger(
                ledger, patient_examination_uuid
            )
        raise ValueError(
            "Validation requires typed patient state via `p_examination` or "
            "`ledger` with `patient_examination_uuid`."
        )

    def evaluate_report_template_validators(
        self,
        name: str,
        p_examination: PExamination | None = None,
        ledger: Ledger | None = None,
        patient_examination_uuid: str | None = None,
        *,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> ReportTemplateRuntimeValidationResultDataDict:
        """
        Execute report-template validators against typed ledger state.

        Parameters:
            name (str): The report template name.
            p_examination (PExamination | None): Typed ledger examination instance.
            ledger (Ledger | None): Typed ledger instance.
            patient_examination_uuid (str | None): UUID used with `ledger`.
            language: Issue message language (`de` by default, or `en`).

        Returns:
            ReportTemplateRuntimeValidationResultDataDict: Runtime validator execution result.
        """
        if p_examination is not None:
            self.kb.assert_examination_admissibility(
                p_examination,
                template_name=name,
            )
        elif ledger is not None and patient_examination_uuid is not None:
            self.kb.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid],
                template_name=name,
            )
        template = self.kb.get_report_template(name)
        classification_validators = (
            self.kb.get_report_template_classification_validators(name)
        )
        classification_validator_names = list(
            template.validators.classification_validators
        )
        classification_validator_names.extend(
            [
                validator_name
                for validator_name in classification_validators
                if validator_name not in classification_validator_names
            ]
        )
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        reported_finding_names = {
            str(finding.get("finding"))
            for finding in normalized_reported_findings
            if finding.get("finding")
        }
        explicit_classification_validators = set(
            template.validators.classification_validators
        )
        classification_validator_names = [
            validator_name
            for validator_name in classification_validator_names
            if (
                validator_name in explicit_classification_validators
                or classification_validators[validator_name].finding
                in reported_finding_names
            )
        ]
        return evaluate_report_template_validators_runtime(
            template,
            classification_validators=classification_validators,
            classification_validator_names=classification_validator_names,
            intervention_validators=self.kb.intervention_validator,
            unit_validators=self.kb.unit_validator,
            findings_validators=self.kb.findings_validator,
            examination_validators=self.kb.examination_validator,
            classifications=self.kb.classification,
            classification_choices=self.kb.classification_choice,
            classification_choice_descriptors=self.kb.classification_choice_descriptor,
            interventions=self.kb.intervention,
            units=self.kb.unit,
            reported_findings=normalized_reported_findings,
            language=language,
            display_names=self._validation_display_names(language),
        )

    def evaluate_findings_validator(
        self,
        validator_name: str,
        *,
        p_examination: PExamination | None = None,
        ledger: Ledger | None = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> FindingsValidatorExecutionDataDict:
        if p_examination is not None:
            self.kb.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.kb.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid]
            )
        validator = self.kb.findings_validator[validator_name]
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        return evaluate_findings_validator_runtime(
            validator,
            reported_findings=normalized_reported_findings,
            language=language,
            display_names=self._validation_display_names(language),
        )

    def evaluate_classification_validator(
        self,
        validator_name: str,
        *,
        p_examination: PExamination | None = None,
        ledger: Ledger | None = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> ClassificationValidatorExecutionDataDict:
        if p_examination is not None:
            self.kb.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.kb.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid]
            )
        validator = self.kb.classification_validator[validator_name]
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        return evaluate_classification_validator_runtime(
            validator,
            classifications=self.kb.classification,
            classification_choices=self.kb.classification_choice,
            classification_choice_descriptors=self.kb.classification_choice_descriptor,
            reported_findings=normalized_reported_findings,
            language=language,
            display_names=self._validation_display_names(language),
        )

    def evaluate_intervention_validator(
        self,
        validator_name: str,
        *,
        p_examination: PExamination | None = None,
        ledger: Ledger | None = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> InterventionValidatorExecutionDataDict:
        if p_examination is not None:
            self.kb.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.kb.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid]
            )
        validator = self.kb.intervention_validator[validator_name]
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        return evaluate_intervention_validator_runtime(
            validator,
            interventions=self.kb.intervention,
            reported_findings=normalized_reported_findings,
            language=language,
            display_names=self._validation_display_names(language),
        )

    def evaluate_unit_validator(
        self,
        validator_name: str,
        *,
        p_examination: PExamination | None = None,
        ledger: Ledger | None = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> UnitValidatorExecutionDataDict:
        if p_examination is not None:
            self.kb.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.kb.assert_examination_admissibility(
                ledger.patient_examinations[patient_examination_uuid]
            )
        validator = self.kb.unit_validator[validator_name]
        normalized_reported_findings = self._normalized_runtime_findings_for_validation(
            p_examination=p_examination,
            ledger=ledger,
            patient_examination_uuid=patient_examination_uuid,
        )
        return evaluate_unit_validator_runtime(
            validator,
            units=self.kb.unit,
            reported_findings=normalized_reported_findings,
            language=language,
            display_names=self._validation_display_names(language),
        )

    def evaluate_examination_validator(
        self,
        validator_name: str,
        *,
        p_examination: PExamination | None = None,
        ledger: Ledger | None = None,
        patient_examination_uuid: str | None = None,
        language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
    ) -> ExaminationValidatorExecutionDataDict:
        if p_examination is not None:
            self.kb.assert_examination_admissibility(p_examination)
        elif ledger is not None and patient_examination_uuid is not None:
            self.kb.assert_examination_admissibility(
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
            classification_validators=self.kb.classification_validator,
            classification_validator_names=[],
            intervention_validators=self.kb.intervention_validator,
            unit_validators=self.kb.unit_validator,
            findings_validators=self.kb.findings_validator,
            examination_validators=self.kb.examination_validator,
            classifications=self.kb.classification,
            classification_choices=self.kb.classification_choice,
            classification_choice_descriptors=self.kb.classification_choice_descriptor,
            interventions=self.kb.intervention,
            units=self.kb.unit,
            reported_findings=normalized_reported_findings,
            language=language,
            display_names=self._validation_display_names(language),
        )
        return result["examination_validators"][0]

    def get_report_template_classification_validators(
        self, name: str
    ) -> dict[str, ClassificationValidator]:
        template = self.kb.get_report_template(name)

        validators_by_name: dict[str, ClassificationValidator] = {}
        explicit_keys: set[tuple[str, str]] = set()
        for validator_name in template.validators.classification_validators:
            validator = self.kb._lookup_optional(
                collection_name="classification_validator",
                key=validator_name,
                source="get_report_template_classification_validators",
            )
            if validator is None:
                continue
            validators_by_name[validator_name] = validator
            explicit_keys.add((validator.finding, validator.classification))

        for section_name in template.report_sections:
            section = self.kb._lookup_optional(
                collection_name="report_template_section",
                key=section_name,
                source="get_report_template_classification_validators",
            )
            if section is None:
                continue
            for finding_ref in section.findings:
                if isinstance(finding_ref, str):
                    report_finding = self.kb._lookup_optional(
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
