"""Ledger admissibility against knowledge-base terminology and template requirements."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
)

from lx_dtypes.models.descriptor_value import DescriptorValue
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import (
    ReportTemplateClassificationRequirement,
    ReportTemplateFindingRequirement,
)
from lx_dtypes.models.knowledge_base.validators.FindingsValidator import (
    FindingsValidator,
)

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
    from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding
    from lx_dtypes.models.ledger.p_finding_classification_choice.Pydantic import (
        PFindingClassificationChoice,
    )
    from lx_dtypes.models.ledger.p_indication.Pydantic import PIndication
    from lx_dtypes.models.ledger.p_indication_classification.Pydantic import (
        PIndicationClassification,
    )


class SemanticAdmissibilityError(ValueError):
    """
    Raised when a structurally valid ledger instance violates KnowledgeBase semantics.
    """


class KnowledgeBaseAdmissibility:
    """Ledger admissibility against knowledge-base terminology and template requirements."""

    def __init__(self, kb: KnowledgeBase) -> None:
        self.kb = kb

    @staticmethod
    def _names_as_list(value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return [item for item in value if item]
        if value:
            return [value]
        return []

    @staticmethod
    def _ensure_finding_requirement(
        requirements: dict[str, ReportTemplateFindingRequirement],
        finding_name: str,
    ) -> None:
        requirements.setdefault(
            finding_name,
            ReportTemplateFindingRequirement(finding=finding_name),
        )

    @classmethod
    def _ensure_classification_requirement(
        cls,
        requirements: dict[str, ReportTemplateFindingRequirement],
        finding_name: str,
        classification_name: str,
    ) -> None:
        cls._ensure_finding_requirement(requirements, finding_name)
        requirement = requirements[finding_name]
        if any(
            existing.classification == classification_name
            for existing in requirement.classifications
        ):
            return
        requirement.classifications.append(
            ReportTemplateClassificationRequirement(classification=classification_name)
        )

    def _add_finding_validator_requirements(
        self,
        requirements: dict[str, ReportTemplateFindingRequirement],
        finding_validator: FindingsValidator,
    ) -> None:
        self._ensure_finding_requirement(requirements, finding_validator.finding)
        condition = finding_validator.query.condition
        if condition is None:
            return
        for requirement_reference in condition.then_requires:
            if requirement_reference.kind == "classification":
                self._ensure_classification_requirement(
                    requirements,
                    finding_validator.finding,
                    requirement_reference.classification or requirement_reference.name,
                )

    def _collect_examination_validator_requirements(
        self,
        requirements: dict[str, ReportTemplateFindingRequirement],
        validator_name: str,
        visited: set[str],
    ) -> None:
        if validator_name in visited:
            return
        visited.add(validator_name)
        examination_validator = self.kb._lookup_optional(
            collection_name="examination_validator",
            key=validator_name,
            source="assert_examination_admissibility",
        )
        if examination_validator is None:
            return

        for finding_validator_name in self._names_as_list(
            examination_validator.finding_validators
        ):
            finding_validator = self.kb._lookup_optional(
                collection_name="findings_validator",
                key=finding_validator_name,
                source="assert_examination_admissibility",
            )
            if finding_validator is not None:
                self._add_finding_validator_requirements(
                    requirements, finding_validator
                )
        for nested_name in self._names_as_list(
            examination_validator.examination_validators
        ):
            self._collect_examination_validator_requirements(
                requirements, nested_name, visited
            )

    def _template_requirements_by_finding(
        self,
        template_name: str,
    ) -> dict[str, ReportTemplateFindingRequirement]:
        template = self.kb.get_report_template(template_name)
        requirements: dict[str, ReportTemplateFindingRequirement] = {}

        for section_name in template.report_sections:
            section = self.kb._lookup_optional(
                collection_name="report_template_section",
                key=section_name,
                source="assert_examination_admissibility",
            )
            if section is None:
                continue
            for finding_ref in section.findings:
                if isinstance(finding_ref, str):
                    report_finding = self.kb._lookup_optional(
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

        for validator_name in self._names_as_list(
            template.validators.findings_validators
        ):
            finding_validator = self.kb._lookup_optional(
                collection_name="findings_validator",
                key=validator_name,
                source="assert_examination_admissibility",
            )
            if finding_validator is not None:
                self._add_finding_validator_requirements(
                    requirements, finding_validator
                )

        for validator_name in self._names_as_list(
            template.validators.classification_validators
        ):
            classification_validator = self.kb._lookup_optional(
                collection_name="classification_validator",
                key=validator_name,
                source="assert_examination_admissibility",
            )
            if classification_validator is not None:
                self._ensure_classification_requirement(
                    requirements,
                    classification_validator.finding,
                    classification_validator.classification,
                )

        visited: set[str] = set()
        for validator_name in self._names_as_list(
            template.validators.examination_validators
        ):
            self._collect_examination_validator_requirements(
                requirements, validator_name, visited
            )
        return requirements

    def _requirements_for_examination(
        self,
        p_examination: PExamination,
        template_name: str | None,
    ) -> dict[str, ReportTemplateFindingRequirement]:
        if template_name is not None:
            template = self.kb.get_report_template(template_name)
            if template.examination != p_examination.examination:
                raise SemanticAdmissibilityError(
                    "PExamination examination "
                    f"'{p_examination.examination}' does not match report template "
                    f"'{template_name}' examination '{template.examination}'."
                )
            return self._template_requirements_by_finding(template_name)

        requirements: dict[str, ReportTemplateFindingRequirement] = {}
        examination = self.kb._lookup_optional(
            collection_name="examination",
            key=p_examination.examination,
            source="assert_examination_admissibility",
        )
        if examination is not None:
            for finding_name in self._names_as_list(examination.findings):
                self._ensure_finding_requirement(requirements, finding_name)

        matching_templates = [
            template
            for template in self.kb.report_template.values()
            if template.examination == p_examination.examination
        ]
        for template in matching_templates:
            requirements.update(self._template_requirements_by_finding(template.name))
        if examination is None and not matching_templates:
            raise SemanticAdmissibilityError(
                f"Unknown examination '{p_examination.examination}'."
            )
        return requirements

    def _assert_descriptor_value(self, name: str, value: DescriptorValue) -> None:
        definition = self.kb.classification_choice_descriptor.get(name)
        if definition is not None:
            try:
                definition.validate_value(value)
            except ValueError as error:
                raise SemanticAdmissibilityError(
                    f"Invalid value for classification choice descriptor '{name}'."
                ) from error

    def _assert_finding_classification_choice(
        self,
        finding_name: str,
        choice: PFindingClassificationChoice,
        allowed_classifications: set[str],
    ) -> None:
        kb_classification = self.kb._lookup_optional(
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
                f"Classification '{choice.classification}' is not permitted for "
                f"finding '{finding_name}'."
            )

        allowed_choices = (
            set(self._names_as_list(kb_classification.classification_choices))
            if kb_classification is not None
            else set()
        )
        kb_choice = self.kb._lookup_optional(
            collection_name="classification_choice",
            key=choice.classification_choice,
            source="assert_examination_admissibility",
        )
        if kb_choice is None and allowed_choices:
            raise SemanticAdmissibilityError(
                f"Unknown classification choice '{choice.classification_choice}'."
            )
        if allowed_choices and choice.classification_choice not in allowed_choices:
            raise SemanticAdmissibilityError(
                f"Classification choice '{choice.classification_choice}' is not "
                f"permitted for classification '{choice.classification}'."
            )

        allowed_descriptors = (
            set(self._names_as_list(kb_choice.classification_choice_descriptors))
            if kb_choice is not None
            else set()
        )
        for descriptor in choice.patient_finding_classification_choice_descriptors:
            descriptor_name = descriptor.classification_choice_descriptor
            if (
                descriptor_name not in self.kb.classification_choice_descriptor
                and allowed_descriptors
            ):
                raise SemanticAdmissibilityError(
                    f"Unknown classification choice descriptor '{descriptor_name}'."
                )
            if allowed_descriptors and descriptor_name not in allowed_descriptors:
                raise SemanticAdmissibilityError(
                    f"Classification choice descriptor '{descriptor_name}' is not "
                    "permitted for classification choice "
                    f"'{choice.classification_choice}'."
                )
            self._assert_descriptor_value(descriptor_name, descriptor.descriptor_value)

    def _assert_finding_admissibility(
        self,
        p_finding: PFinding,
        examination_name: str,
        allowed_findings: set[str],
        requirements: dict[str, ReportTemplateFindingRequirement],
    ) -> None:
        kb_finding = self.kb._lookup_optional(
            collection_name="finding",
            key=p_finding.finding,
            source="assert_examination_admissibility",
        )
        requirement = requirements.get(p_finding.finding)
        if allowed_findings and p_finding.finding not in allowed_findings:
            raise SemanticAdmissibilityError(
                f"Finding '{p_finding.finding}' is not permitted for examination "
                f"'{examination_name}'."
            )
        if kb_finding is None and requirement is None:
            raise SemanticAdmissibilityError(f"Unknown finding '{p_finding.finding}'.")

        allowed_classifications = (
            set(self._names_as_list(kb_finding.classifications))
            if kb_finding is not None
            else set()
        )
        if requirement is not None:
            allowed_classifications.update(
                item.classification for item in requirement.classifications
            )
        allowed_interventions = (
            set(self._names_as_list(kb_finding.interventions))
            if kb_finding is not None
            else set()
        )

        for classifications in p_finding.patient_finding_classifications:
            for choice in classifications.patient_finding_classification_choices:
                self._assert_finding_classification_choice(
                    p_finding.finding, choice, allowed_classifications
                )
        for interventions in p_finding.patient_finding_interventions:
            for intervention in interventions.patient_finding_interventions:
                if intervention.intervention not in self.kb.intervention:
                    raise SemanticAdmissibilityError(
                        f"Unknown intervention '{intervention.intervention}'."
                    )
                if intervention.intervention not in allowed_interventions:
                    raise SemanticAdmissibilityError(
                        f"Intervention '{intervention.intervention}' is not "
                        f"permitted for finding '{p_finding.finding}'."
                    )

    def _assert_indication_classification(
        self,
        indication_name: str,
        classification: PIndicationClassification,
        allowed_classifications: set[str],
    ) -> None:
        kb_classification = self.kb.classification.get(classification.classification)
        if (
            kb_classification is None
            and classification.classification not in allowed_classifications
        ):
            raise SemanticAdmissibilityError(
                f"Unknown indication classification '{classification.classification}'."
            )
        if classification.classification not in allowed_classifications:
            raise SemanticAdmissibilityError(
                f"Classification '{classification.classification}' is not "
                f"permitted for indication '{indication_name}'."
            )

        allowed_choices = (
            set(self._names_as_list(kb_classification.classification_choices))
            if kb_classification is not None
            else set()
        )
        kb_choice = self.kb.classification_choice.get(
            classification.classification_choice
        )
        if kb_choice is None and allowed_choices:
            raise SemanticAdmissibilityError(
                "Unknown indication classification choice "
                f"'{classification.classification_choice}'."
            )
        if (
            allowed_choices
            and classification.classification_choice not in allowed_choices
        ):
            raise SemanticAdmissibilityError(
                f"Classification choice '{classification.classification_choice}' "
                "is not permitted for classification "
                f"'{classification.classification}'."
            )

        allowed_descriptors = (
            set(self._names_as_list(kb_choice.classification_choice_descriptors))
            if kb_choice is not None
            else set()
        )
        for descriptor in classification.patient_indication_classification_descriptors:
            descriptor_name = descriptor.classification_choice_descriptor
            if (
                descriptor_name not in self.kb.classification_choice_descriptor
                and allowed_descriptors
            ):
                raise SemanticAdmissibilityError(
                    "Unknown indication classification choice descriptor "
                    f"'{descriptor_name}'."
                )
            if allowed_descriptors and descriptor_name not in allowed_descriptors:
                raise SemanticAdmissibilityError(
                    f"Classification choice descriptor '{descriptor_name}' is not "
                    "permitted for classification choice "
                    f"'{classification.classification_choice}'."
                )
            self._assert_descriptor_value(descriptor_name, descriptor.descriptor_value)

    def _assert_indication_admissibility(
        self,
        p_indication: PIndication,
        examination_name: str,
        allowed_indications: set[str],
    ) -> None:
        kb_indication = self.kb.indication.get(p_indication.indication)
        if kb_indication is None:
            raise SemanticAdmissibilityError(
                f"Unknown indication '{p_indication.indication}'."
            )
        if allowed_indications and p_indication.indication not in allowed_indications:
            raise SemanticAdmissibilityError(
                f"Indication '{p_indication.indication}' is not permitted for "
                f"examination '{examination_name}'."
            )

        allowed_classifications = set(
            self._names_as_list(kb_indication.classifications)
        )
        for classification in p_indication.patient_indication_classifications:
            self._assert_indication_classification(
                p_indication.indication, classification, allowed_classifications
            )

    def assert_examination_admissibility(
        self,
        p_examination: PExamination,
        *,
        template_name: str | None = None,
    ) -> None:
        requirements_by_finding = self._requirements_for_examination(
            p_examination, template_name
        )
        allowed_findings = set(requirements_by_finding.keys())
        examination = self.kb.examination.get(p_examination.examination)
        allowed_indications = (
            set(self._names_as_list(examination.indications))
            if examination is not None
            else set()
        )
        for p_finding in p_examination.patient_findings:
            self._assert_finding_admissibility(
                p_finding,
                p_examination.examination,
                allowed_findings,
                requirements_by_finding,
            )

        for p_indication in p_examination.patient_indications:
            self._assert_indication_admissibility(
                p_indication, p_examination.examination, allowed_indications
            )
