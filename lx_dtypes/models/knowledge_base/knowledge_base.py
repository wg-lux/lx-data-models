from pathlib import Path
from typing import Any, Dict, Optional, Self, Union

import yaml
from pydantic import Field, field_serializer

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
    UnitShallow,
    UnitTypeShallow,
)
from lx_dtypes.utils.mixins.base_model import BaseModelMixin


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
    units: Dict[str, "UnitShallow"] = Field(default_factory=dict)
    unit_types: Dict[str, "UnitTypeShallow"] = Field(default_factory=dict)

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
                elif isinstance(parsed_object, InformationSourceShallow):
                    kb.information_sources[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, UnitShallow):
                    kb.units[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, UnitTypeShallow):  # type: ignore
                    kb.unit_types[parsed_object.name] = parsed_object
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
        self.units.update(other.units)
        self.unit_types.update(other.unit_types)

    def export_yaml(self, export_dir: Path, filename: str = "knowledge_base") -> None:
        """Export the knowledge base to the specified directory.

        Args:
            export_dir (Path): The directory to export the knowledge base to.
        """
        from lx_dtypes.utils.export.export_knowledge_base import export_knowledge_base

        export_knowledge_base(self, export_dir, filename=filename)

    @classmethod
    def create_from_yaml(cls, yaml_path: Path) -> Self:
        """Load a knowledge base from a YAML dump.

        Args:
            yaml_path (Path): The path to the YAML file.
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            data_dict = yaml.safe_load(f)

        kb = cls.model_validate(data_dict)
        return kb

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

    @field_serializer("citations")
    def serialize_citations(
        self, citations: Dict[str, "CitationShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: citation.model_dump() for name, citation in citations.items()
        }
        return r

    @field_serializer("findings")
    def serialize_findings(
        self, findings: Dict[str, "FindingShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: finding.model_dump() for name, finding in findings.items()
        }
        return r

    @field_serializer("finding_types")
    def serialize_finding_types(
        self, finding_types: Dict[str, "FindingTypeShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: finding_type.model_dump()
            for name, finding_type in finding_types.items()
        }
        return r

    @field_serializer("classifications")
    def serialize_classifications(
        self, classifications: Dict[str, "ClassificationShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: classification.model_dump()
            for name, classification in classifications.items()
        }
        return r

    @field_serializer("classification_types")
    def serialize_classification_types(
        self, classification_types: Dict[str, "ClassificationTypeShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: classification_type.model_dump()
            for name, classification_type in classification_types.items()
        }
        return r

    @field_serializer("classification_choices")
    def serialize_classification_choices(
        self, classification_choices: Dict[str, "ClassificationChoiceShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: classification_choice.model_dump()
            for name, classification_choice in classification_choices.items()
        }
        return r

    @field_serializer("examinations")
    def serialize_examinations(
        self, examinations: Dict[str, "ExaminationShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: examination.model_dump() for name, examination in examinations.items()
        }
        return r

    @field_serializer("examination_types")
    def serialize_examination_types(
        self, examination_types: Dict[str, "ExaminationTypeShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: examination_type.model_dump()
            for name, examination_type in examination_types.items()
        }
        return r

    @field_serializer("interventions")
    def serialize_interventions(
        self, interventions: Dict[str, "InterventionShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: intervention.model_dump()
            for name, intervention in interventions.items()
        }
        return r

    @field_serializer("intervention_types")
    def serialize_intervention_types(
        self, intervention_types: Dict[str, "InterventionTypeShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: intervention_type.model_dump()
            for name, intervention_type in intervention_types.items()
        }
        return r

    @field_serializer("indications")
    def serialize_indications(
        self, indications: Dict[str, "IndicationShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: indication.model_dump() for name, indication in indications.items()
        }
        return r

    @field_serializer("indication_types")
    def serialize_indication_types(
        self, indication_types: Dict[str, "IndicationTypeShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: indication_type.model_dump()
            for name, indication_type in indication_types.items()
        }
        return r

    @field_serializer("information_sources")
    def serialize_information_sources(
        self, information_sources: Dict[str, "InformationSourceShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: information_source.model_dump()
            for name, information_source in information_sources.items()
        }
        return r

    @field_serializer("config")
    def serialize_config(
        self, config: Optional["KnowledgeBaseConfig"]
    ) -> Optional[Dict[str, Any]]:
        if config is None:
            return None
        return config.model_dump()

    @field_serializer("units")
    def serialize_units(self, units: Dict[str, "UnitShallow"]) -> Dict[str, Any]:
        r: Dict[str, Any] = {name: unit.model_dump() for name, unit in units.items()}
        return r

    @field_serializer("unit_types")
    def serialize_unit_types(
        self, unit_types: Dict[str, "UnitTypeShallow"]
    ) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            name: unit_type.model_dump() for name, unit_type in unit_types.items()
        }
        return r
