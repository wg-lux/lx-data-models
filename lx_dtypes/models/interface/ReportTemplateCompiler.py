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
            "examination": template.examination,
            "report_sections": [self._resolve_section(s) for s in template.report_sections],
            "validators": self._resolve_all_validators(template),
        }

    def _resolve_section(self, section_name: str) -> Dict[str, Any]:
        section = self.kb.report_template_section.get(section_name)
        if not section:
            if self.tolerant: return {"name": section_name, "missing": True}
            raise KeyError(f"Section {section_name} not found")

        return {
            "name": section.name,
            "position": section.position,
            "types": section.types,
            "section_kind": section.section_kind,
            "fields": [f.model_dump() for f in section.fields],
            "findings": [self._resolve_finding_requirement(fr) for fr in section.findings],
        }

    def _resolve_finding_requirement(self, ref: Union[str, Any]) -> Dict[str, Any]:
        # Handle the polymorphism: is it a string ID or a Requirement object?
        if isinstance(ref, str):
            if ref in self.kb.report_finding:
                return self.kb.report_finding[ref].as_requirement().model_dump()
            return {"finding": ref} # Bare finding reference
        return cast(Dict[str, Any], ref.model_dump())

    def _resolve_all_validators(self, template: Any) -> Dict[str, List[Any]]:
        v = template.validators
        return {
            "examination_validators": self._hydrate_list(v.examination_validators, self.kb.examination_validator),
            "classification_validators": self._hydrate_list(v.classification_validators, self.kb.classification_validator),
            "intervention_validators": self._hydrate_list(v.intervention_validators, self.kb.intervention_validator),
            "unit_validators": self._hydrate_list(v.unit_validators, self.kb.unit_validator),
            "findings_validators": self._hydrate_list(v.findings_validators, self.kb.findings_validator),
        }

    def _hydrate_list(self, names: Iterable[str], registry: Dict[str, Any]) -> List[Any]:
        resolved = []
        for name in names:
            if name in registry:
                resolved.append(registry[name].model_dump())
            elif self.tolerant:
                resolved.append(name)
        return resolved
