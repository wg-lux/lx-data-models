from math import isfinite
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Union, cast

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase


class ReportTemplateCompiler:
    """
    A specialized engine to transform a normalized KnowledgeBase
    into a hydrated, hierarchical Report Template payload.
    """

    def __init__(self, kb: "KnowledgeBase", tolerant: bool = True):
        self.kb = kb
        self.tolerant = tolerant

    def compile(self, template_name: str) -> Dict[str, Any]:
        template = self.kb.get_report_template(template_name)

        return {
            "name": template.name,
            "name_de": template.name_de,
            "name_en": template.name_en,
            "description": template.description,
            "version": template.version,
            "guideline_references": [
                reference.model_dump(mode="json")
                for reference in template.guideline_references
            ],
            "coverage_version": template.coverage_version,
            "coverage_concepts": [
                concept.model_dump(mode="json")
                for concept in template.coverage_concepts
            ],
            "examination": template.examination,
            "report_sections": [
                self._resolve_section(s) for s in template.report_sections
            ],
            "validators": self._resolve_all_validators(template),
        }

    def _resolve_section(self, section_name: str) -> Dict[str, Any]:
        section = self.kb.report_template_section.get(section_name)
        if not section:
            if self.tolerant:
                return {"name": section_name, "missing": True}
            raise KeyError(f"Section {section_name} not found")

        return {
            "name": section.name,
            "position": section.position,
            "types": section.types,
            "section_kind": section.section_kind,
            "fields": [f.model_dump() for f in section.fields],
            "findings": [
                self._resolve_finding_requirement(fr) for fr in section.findings
            ],
        }

    def _resolve_finding_requirement(self, ref: Union[str, Any]) -> Dict[str, Any]:
        # Handle the polymorphism: is it a string ID or a Requirement object?
        if isinstance(ref, str):
            if ref in self.kb.report_finding:
                requirement = self.kb.report_finding[ref].as_requirement().model_dump()
                return self._hydrate_finding_inputs(requirement)
            return {"finding": ref}  # Bare finding reference
        requirement = cast(Dict[str, Any], ref.model_dump())
        return self._hydrate_finding_inputs(requirement)

    def _hydrate_finding_inputs(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """Expose the KB-defined input contract for every requested classification."""

        hydrated = dict(requirement)
        raw_requirements = hydrated.get("classifications", [])
        classification_requirements: List[Dict[str, Any]] = []
        for raw_requirement in raw_requirements:
            item = dict(raw_requirement)
            classification_name = str(item.get("classification", "")).strip()
            classification = self.kb.classification.get(classification_name)
            if classification is None:
                classification_requirements.append(item)
                continue

            choices: List[Dict[str, Any]] = []
            raw_choice_names = classification.classification_choices
            choice_names = (
                [raw_choice_names]
                if isinstance(raw_choice_names, str)
                else raw_choice_names
            )
            for choice_name in choice_names:
                choice = self.kb.classification_choice.get(choice_name)
                if choice is None:
                    continue
                descriptors: List[Dict[str, Any]] = []
                raw_descriptor_names = choice.classification_choice_descriptors
                descriptor_names = (
                    [raw_descriptor_names]
                    if isinstance(raw_descriptor_names, str)
                    else raw_descriptor_names
                )
                for descriptor_name in descriptor_names:
                    descriptor = self.kb.classification_choice_descriptor.get(
                        descriptor_name
                    )
                    if descriptor is None:
                        continue
                    unit_name = descriptor.unit
                    unit = self.kb.unit.get(unit_name)
                    descriptor_type = descriptor.classification_choice_descriptor_type
                    numeric_min = descriptor.numeric_min
                    numeric_max = descriptor.numeric_max
                    descriptors.append(
                        {
                            "name": descriptor.name,
                            "type": getattr(descriptor_type, "value", descriptor_type),
                            "unit": unit_name,
                            "unit_abbreviation": (
                                unit.abbreviation if unit is not None else None
                            ),
                            "numeric_min": (
                                numeric_min if isfinite(numeric_min) else None
                            ),
                            "numeric_max": (
                                numeric_max if isfinite(numeric_max) else None
                            ),
                        }
                    )
                choices.append({"name": choice.name, "descriptors": descriptors})

            item["input"] = {"choices": choices}
            classification_requirements.append(item)

        hydrated["classifications"] = classification_requirements
        return hydrated

    def _resolve_all_validators(self, template: Any) -> Dict[str, List[Any]]:
        v = template.validators
        return {
            "examination_validators": self._hydrate_list(
                v.examination_validators, self.kb.examination_validator
            ),
            "classification_validators": self._hydrate_list(
                v.classification_validators, self.kb.classification_validator
            ),
            "intervention_validators": self._hydrate_list(
                v.intervention_validators, self.kb.intervention_validator
            ),
            "unit_validators": self._hydrate_list(
                v.unit_validators, self.kb.unit_validator
            ),
            "findings_validators": self._hydrate_list(
                v.findings_validators, self.kb.findings_validator
            ),
        }

    def _hydrate_list(
        self, names: Iterable[str], registry: Dict[str, Any]
    ) -> List[Any]:
        resolved = []
        for name in names:
            if name in registry:
                resolved.append(registry[name].model_dump())
            elif self.tolerant:
                resolved.append(name)
        return resolved
