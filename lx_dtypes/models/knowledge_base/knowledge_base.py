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
    classification_types: Dict[str, "ClassificationTypeShallow"] = Field(
        default_factory=dict
    )
    classification_choices: Dict[str, "ClassificationChoiceShallow"] = Field(
        default_factory=dict
    )
    examinations: Dict[str, "ExaminationShallow"] = Field(default_factory=dict)
    examination_types: Dict[str, "ExaminationTypeShallow"] = Field(default_factory=dict)
    indications: Dict[str, "IndicationShallow"] = Field(default_factory=dict)
    indication_types: Dict[str, "IndicationTypeShallow"] = Field(default_factory=dict)
    interventions: Dict[str, "InterventionShallow"] = Field(default_factory=dict)
    intervention_types: Dict[str, "InterventionTypeShallow"] = Field(
        default_factory=dict
    )
    information_sources: Dict[str, "InformationSourceShallow"] = Field(
        default_factory=dict
    )

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
                    raise TypeError(
                        f"Unsupported shallow model type: {type(parsed_object)}"
                    )
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

    def get_finding(self, name: str) -> "FindingShallow":
        """Get a finding by name.

        Args:
            name (str): The name of the finding.
        Returns:
            FindingShallow: The finding with the given name.
        """
        finding = self.findings.get(name)
        if finding is None:
            raise KeyError(f"Finding '{name}' not found in knowledge base.")
        return finding

    def get_finding_type(self, name: str) -> "FindingTypeShallow":
        """Get a finding type by name.
        Args:
            name (str): The name of the finding type.
        Returns:
            FindingTypeShallow: The finding type with the given name.
        """
        finding_type = self.finding_types.get(name)
        if finding_type is None:
            raise KeyError(f"Finding type '{name}' not found in knowledge base.")
        return finding_type

    def get_classification(self, name: str) -> "ClassificationShallow":
        classification = self.classifications.get(name)
        if classification is None:
            raise KeyError(f"Classification '{name}' not found in knowledge base.")
        return classification

    def get_classification_type(self, name: str) -> "ClassificationTypeShallow":
        classification_type = self.classification_types.get(name)
        if classification_type is None:
            raise KeyError(f"Classification type '{name}' not found in knowledge base.")
        return classification_type

    def get_classification_choice(self, name: str) -> "ClassificationChoiceShallow":
        classification_choice = self.classification_choices.get(name)
        if classification_choice is None:
            raise KeyError(
                f"Classification choice '{name}' not found in knowledge base."
            )
        return classification_choice

    def get_examination(self, name: str) -> "ExaminationShallow":
        """Get an examination by name.

        Args:
            name (str): The name of the examination.
        Returns:
            ExaminationShallow: The examination with the given name.
        """
        examination = self.examinations.get(name)
        if examination is None:
            raise KeyError(f"Examination '{name}' not found in knowledge base.")
        return examination

    def get_examination_type(self, name: str) -> "ExaminationTypeShallow":
        """Get an examination type by name.

        Args:
            name (str): The name of the examination type.
        Returns:
            ExaminationTypeShallow: The examination type with the given name.
        """
        examination_type = self.examination_types.get(name)
        if examination_type is None:
            raise KeyError(f"Examination type '{name}' not found in knowledge base.")
        return examination_type

    def get_intervention(self, name: str) -> "InterventionShallow":
        """Get an intervention by name.

        Args:
            name (str): The name of the intervention.
        Returns:
            InterventionShallow: The intervention with the given name.
        """
        intervention = self.interventions.get(name)
        if intervention is None:
            raise KeyError(f"Intervention '{name}' not found in knowledge base.")
        return intervention

    def get_intervention_type(self, name: str) -> "InterventionTypeShallow":
        """Get an intervention type by name.

        Args:
            name (str): The name of the intervention type.
        Returns:
            InterventionTypeShallow: The intervention type with the given name.
        """
        intervention_type = self.intervention_types.get(name)
        if intervention_type is None:
            raise KeyError(f"Intervention type '{name}' not found in knowledge base.")
        return intervention_type

    def get_indication(self, name: str) -> "IndicationShallow":
        """Get an indication by name.

        Args:
            name (str): The name of the indication.
        Returns:
            IndicationShallow: The indication with the given name.
        """
        indication = self.indications.get(name)
        if indication is None:
            raise KeyError(f"Indication '{name}' not found in knowledge base.")
        return indication

    def get_indication_type(self, name: str) -> "IndicationTypeShallow":
        """Get an indication type by name.

        Args:
            name (str): The name of the indication type.
        Returns:
            IndicationTypeShallow: The indication type with the given name.
        """
        indication_type = self.indication_types.get(name)
        if indication_type is None:
            raise KeyError(f"Indication type '{name}' not found in knowledge base.")
        return indication_type

    def get_information_source(self, name: str) -> "InformationSourceShallow":
        """Get an information source by name.

        Args:
            name (str): The name of the information source.
        Returns:
            InformationSourceShallow: The information source with the given name.
        """
        information_source = self.information_sources.get(name)
        if information_source is None:
            raise KeyError(f"Information source '{name}' not found in knowledge base.")
        return information_source
