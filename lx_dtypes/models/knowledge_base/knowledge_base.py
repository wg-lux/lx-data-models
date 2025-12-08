from pathlib import Path
from typing import Dict, Optional, Union

from pydantic import Field

from lx_dtypes.models.knowledge_base.knowledge_base_config import KnowledgeBaseConfig
from lx_dtypes.models.shallow import (
    CitationShallow,
    ClassificationChoiceShallow,
    ClassificationShallow,
    ClassificationTypeShallow,
    ExaminationShallow,
    ExaminationTypeShallow,
    FindingShallow,
    FindingTypeShallow,
    IndicationShallow,
    IndicationTypeShallow,
    InformationSourceShallow,
    InterventionShallow,
    InterventionTypeShallow,
)
from lx_dtypes.utils.mixins import BaseModelMixin


class KnowledgeBase(BaseModelMixin):
    """
    Model representing a knowledge base.

    """

    config: Optional[KnowledgeBaseConfig] = None

    citations: Dict[str, "CitationShallow"] = Field(default_factory=dict)
    findings: Dict[str, "FindingShallow"] = Field(default_factory=dict)
    finding_types: Dict[str, "FindingTypeShallow"] = Field(default_factory=dict)
    classifications: Dict[str, "ClassificationShallow"] = Field(default_factory=dict)
    classification_types: Dict[str, "ClassificationTypeShallow"] = Field(default_factory=dict)
    classification_choices: Dict[str, "ClassificationChoiceShallow"] = Field(default_factory=dict)
    examinations: Dict[str, "ExaminationShallow"] = Field(default_factory=dict)
    examination_types: Dict[str, "ExaminationTypeShallow"] = Field(default_factory=dict)
    indications: Dict[str, "IndicationShallow"] = Field(default_factory=dict)
    indication_types: Dict[str, "IndicationTypeShallow"] = Field(default_factory=dict)
    interventions: Dict[str, "InterventionShallow"] = Field(default_factory=dict)
    intervention_types: Dict[str, "InterventionTypeShallow"] = Field(default_factory=dict)
    information_sources: Dict[str, "InformationSourceShallow"] = Field(default_factory=dict)

    @classmethod
    def create_from_config(cls, config: "KnowledgeBaseConfig") -> "KnowledgeBase":
        """Create a KnowledgeBase instance from a KnowledgeBaseConfig.

        Args:
            config (KnowledgeBaseConfig): The knowledge base configuration.
        Returns:
            KnowledgeBase: The created KnowledgeBase instance.
        """

        name = config.name
        kb_dict: Dict[str, Union[str, "KnowledgeBaseConfig", Path]] = {
            "config": config,
            "name": name,
        }

        if config.source_file:
            kb_dict["source_file"] = config.source_file

        kb = cls.model_validate(kb_dict)
        data = config.data
        submodule_files = data.get_files_with_suffix(".yaml")
        for sm_file in submodule_files:
            from lx_dtypes.utils.parser import parse_shallow_object

            parsed_object_generator = parse_shallow_object(sm_file)
            for parsed_object in parsed_object_generator:
                if isinstance(parsed_object, CitationShallow):
                    kb.citations[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, FindingShallow):
                    kb.findings[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, FindingTypeShallow):
                    kb.finding_types[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ClassificationShallow):
                    kb.classifications[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ClassificationTypeShallow):
                    kb.classification_types[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ClassificationChoiceShallow):
                    kb.classification_choices[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ExaminationShallow):
                    kb.examinations[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ExaminationTypeShallow):
                    kb.examination_types[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, IndicationShallow):
                    kb.indications[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, IndicationTypeShallow):
                    kb.indication_types[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, InterventionShallow):
                    kb.interventions[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, InterventionTypeShallow):
                    kb.intervention_types[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, InformationSourceShallow):  # type: ignore[unreachable]
                    kb.information_sources[parsed_object.name] = parsed_object
                else:
                    raise TypeError(f"Unsupported shallow model type: {type(parsed_object)}")
        return kb

    def import_knowledge_base(self, other: "KnowledgeBase") -> None:
        """Merge another KnowledgeBase into this one.

        Args:
            other (KnowledgeBase): The other KnowledgeBase to merge.
        """
        self.findings.update(other.findings)
        self.finding_types.update(other.finding_types)
        self.citations.update(other.citations)
        self.classifications.update(other.classifications)
        self.classification_types.update(other.classification_types)
        self.classification_choices.update(other.classification_choices)
        self.examinations.update(other.examinations)
        self.examination_types.update(other.examination_types)
        self.indications.update(other.indications)
        self.indication_types.update(other.indication_types)
        self.interventions.update(other.interventions)
        self.intervention_types.update(other.intervention_types)
        self.information_sources.update(other.information_sources)

    def get_citation(self, name: str) -> "CitationShallow":
        """Get a citation by name.

        Args:
            name (str): The name of the citation.
        Returns:
            CitationShallow: The citation with the given name.
        """
        citation = self.citations.get(name)
        if citation is None:
            raise KeyError(f"Citation '{name}' not found in knowledge base.")
        return citation

    def count_entries(self) -> Dict[str, int]:
        """Count the number of entries in each category of the knowledge base.

        Returns:
            Dict[str, int]: A dictionary with the counts of each category.
        """
        return {
            "citations": len(self.citations),
            "findings": len(self.findings),
            "finding_types": len(self.finding_types),
            "classifications": len(self.classifications),
            "classification_types": len(self.classification_types),
            "classification_choices": len(self.classification_choices),
            "examinations": len(self.examinations),
            "examination_types": len(self.examination_types),
            "indications": len(self.indications),
            "indication_types": len(self.indication_types),
            "interventions": len(self.interventions),
            "intervention_types": len(self.intervention_types),
            "information_sources": len(self.information_sources),
        }
