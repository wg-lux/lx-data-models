from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Self,
    Tuple,
    TypedDict,
    Union,
)

import yaml
from pydantic import Field, field_serializer

from lx_dtypes.models.base_models.base_model import (
    AppBaseModelNamesUUIDTags,
)
from lx_dtypes.models.core import (
    CitationShallow,
    CitationShallowDataDict,
    ClassificationChoiceDescriptorShallow,
    ClassificationChoiceDescriptorShallowDataDict,
    ClassificationChoiceShallow,
    ClassificationChoiceShallowDataDict,
    ClassificationShallow,
    ClassificationShallowDataDict,
    ClassificationTypeShallow,
    ClassificationTypeShallowDataDict,
    ExaminationShallow,
    ExaminationShallowDataDict,
    ExaminationTypeShallow,
    ExaminationTypeShallowDataDict,
    FindingShallow,
    FindingShallowDataDict,
    FindingTypeShallow,
    FindingTypeShallowDataDict,
    IndicationShallow,
    IndicationShallowDataDict,
    IndicationTypeShallow,
    IndicationTypeShallowDataDict,
    InformationSourceShallow,
    InformationSourceShallowDataDict,
    InterventionShallow,
    InterventionShallowDataDict,
    InterventionTypeShallow,
    InterventionTypeShallowDataDict,
    UnitShallow,
    UnitShallowDataDict,
    UnitTypeShallow,
    UnitTypeShallowDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.typing.pydantic.knowledge_base_shallow import (
        KB_SHALLOW_UNION_PYDANTIC_LIST,
    )
#     from lx_dtypes.stats.dataset import KnowledgeBaseDataset
from lx_dtypes.models.knowledge_base.knowledge_base_config import KnowledgeBaseConfig
from lx_dtypes.utils.factories.field_defaults import str_unknown_factory


class KnowledgeBaseRecordLists(TypedDict):
    citations: List[CitationShallowDataDict]
    findings: List[FindingShallowDataDict]
    finding_types: List[FindingTypeShallowDataDict]
    classifications: List[ClassificationShallowDataDict]
    classification_types: List[ClassificationTypeShallowDataDict]
    classification_choices: List[ClassificationChoiceShallowDataDict]
    classification_choice_descriptors: List[
        ClassificationChoiceDescriptorShallowDataDict
    ]
    examinations: List[ExaminationShallowDataDict]
    examination_types: List[ExaminationTypeShallowDataDict]
    indications: List[IndicationShallowDataDict]
    indication_types: List[IndicationTypeShallowDataDict]
    interventions: List[InterventionShallowDataDict]
    intervention_types: List[InterventionTypeShallowDataDict]
    information_sources: List[InformationSourceShallowDataDict]
    units: List[UnitShallowDataDict]
    unit_types: List[UnitTypeShallowDataDict]


class KnowledgeBaseDataDict(TypedDict):
    config: Optional[Dict[str, Any]]
    citations: Dict[str, CitationShallowDataDict]
    findings: Dict[str, FindingShallowDataDict]
    finding_types: Dict[str, FindingTypeShallowDataDict]
    classifications: Dict[str, ClassificationShallowDataDict]
    classification_types: Dict[str, ClassificationTypeShallowDataDict]
    classification_choices: Dict[str, ClassificationChoiceShallowDataDict]
    classification_choice_descriptors: Dict[
        str, ClassificationChoiceDescriptorShallowDataDict
    ]
    examinations: Dict[str, ExaminationShallowDataDict]
    examination_types: Dict[str, ExaminationTypeShallowDataDict]
    indications: Dict[str, IndicationShallowDataDict]
    indication_types: Dict[str, IndicationTypeShallowDataDict]
    interventions: Dict[str, InterventionShallowDataDict]
    intervention_types: Dict[str, InterventionTypeShallowDataDict]
    information_sources: Dict[str, InformationSourceShallowDataDict]
    units: Dict[str, UnitShallowDataDict]
    unit_types: Dict[str, UnitTypeShallowDataDict]


class KnowledgeBase(AppBaseModelNamesUUIDTags):
    """
    Model representing a knowledge base.

    """

    config: Optional[KnowledgeBaseConfig] = None

    citation: Dict[str, "CitationShallow"] = Field(default_factory=dict)
    finding: Dict[str, "FindingShallow"] = Field(default_factory=dict)
    finding_type: Dict[str, "FindingTypeShallow"] = Field(default_factory=dict)
    classification: Dict[str, "ClassificationShallow"] = Field(default_factory=dict)
    classification_type: Dict[str, "ClassificationTypeShallow"] = Field(
        default_factory=dict
    )
    classification_choice: Dict[str, "ClassificationChoiceShallow"] = Field(
        default_factory=dict
    )
    classification_choice_descriptor: Dict[
        str, "ClassificationChoiceDescriptorShallow"
    ] = Field(default_factory=dict)
    examination: Dict[str, "ExaminationShallow"] = Field(default_factory=dict)
    examination_type: Dict[str, "ExaminationTypeShallow"] = Field(default_factory=dict)
    indication: Dict[str, "IndicationShallow"] = Field(default_factory=dict)
    indication_type: Dict[str, "IndicationTypeShallow"] = Field(default_factory=dict)
    intervention: Dict[str, "InterventionShallow"] = Field(default_factory=dict)
    intervention_type: Dict[str, "InterventionTypeShallow"] = Field(
        default_factory=dict
    )
    information_source: Dict[str, "InformationSourceShallow"] = Field(
        default_factory=dict
    )
    unit: Dict[str, "UnitShallow"] = Field(default_factory=dict)
    unit_type: Dict[str, "UnitTypeShallow"] = Field(default_factory=dict)

    @property
    def ddict(self) -> type[KnowledgeBaseDataDict]:
        return KnowledgeBaseDataDict

    @property
    def config_safe(self) -> KnowledgeBaseConfig:
        """Get the knowledge base config, raising an error if it is not set.

        Returns:
            KnowledgeBaseConfig: The knowledge base config.
        """
        if self.config is None:
            raise ValueError("KnowledgeBase config is not set.")
        return self.config

    def to_ddict(self) -> KnowledgeBaseDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

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

            parsed_object_generator = parse_shallow_object(sm_file, kb_module_name=name)
            for parsed_object in parsed_object_generator:
                if isinstance(parsed_object, CitationShallow):
                    kb.citation[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, FindingShallow):
                    kb.finding[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, FindingTypeShallow):
                    kb.finding_type[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ClassificationShallow):
                    kb.classification[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ClassificationTypeShallow):
                    kb.classification_type[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ClassificationChoiceShallow):
                    kb.classification_choice[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ClassificationChoiceDescriptorShallow):
                    kb.classification_choice_descriptor[parsed_object.name] = (
                        parsed_object
                    )

                elif isinstance(parsed_object, ExaminationShallow):
                    kb.examination[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, ExaminationTypeShallow):
                    kb.examination_type[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, IndicationShallow):
                    kb.indication[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, IndicationTypeShallow):
                    kb.indication_type[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, InterventionShallow):
                    kb.intervention[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, InterventionTypeShallow):
                    kb.intervention_type[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, InformationSourceShallow):
                    kb.information_source[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, UnitShallow):
                    kb.unit[parsed_object.name] = parsed_object
                elif isinstance(parsed_object, UnitTypeShallow):  # type: ignore
                    kb.unit_type[parsed_object.name] = parsed_object
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
        self.finding.update(other.finding)
        self.finding_type.update(other.finding_type)
        self.citation.update(other.citation)
        self.classification.update(other.classification)
        self.classification_type.update(other.classification_type)
        self.classification_choice.update(other.classification_choice)
        self.classification_choice_descriptor.update(
            other.classification_choice_descriptor
        )
        self.examination.update(other.examination)
        self.examination_type.update(other.examination_type)
        self.indication.update(other.indication)
        self.indication_type.update(other.indication_type)
        self.intervention.update(other.intervention)
        self.intervention_type.update(other.intervention_type)
        self.information_source.update(other.information_source)
        self.unit.update(other.unit)
        self.unit_type.update(other.unit_type)

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
            "citation": len(self.citation),
            "finding": len(self.finding),
            "finding_type": len(self.finding_type),
            "classification": len(self.classification),
            "classification_type": len(self.classification_type),
            "classification_choice": len(self.classification_choice),
            "examination": len(self.examination),
            "examination_type": len(self.examination_type),
            "indication": len(self.indication),
            "indication_type": len(self.indication_type),
            "intervention": len(self.intervention),
            "intervention_type": len(self.intervention_type),
            "information_source": len(self.information_source),
            "unit": len(self.unit),
            "unit_type": len(self.unit_type),
            "classification_choice_descriptor": len(
                self.classification_choice_descriptor
            ),
        }

    def get_citation(self, name: str) -> "CitationShallow":
        """Get a citation by name.

        Args:
            name (str): The name of the citation.
        Returns:
            CitationShallow: The citation with the given name.
        """
        citation = self.citation.get(name)
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
        finding = self.finding.get(name)
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
        finding_type = self.finding_type.get(name)
        if finding_type is None:
            raise KeyError(f"Finding type '{name}' not found in knowledge base.")
        return finding_type

    def get_classification(self, name: str) -> "ClassificationShallow":
        classification = self.classification.get(name)
        if classification is None:
            raise KeyError(f"Classification '{name}' not found in knowledge base.")
        return classification

    def get_classification_type(self, name: str) -> "ClassificationTypeShallow":
        classification_type = self.classification_type.get(name)
        if classification_type is None:
            raise KeyError(f"Classification type '{name}' not found in knowledge base.")
        return classification_type

    def get_classification_choice(self, name: str) -> "ClassificationChoiceShallow":
        classification_choice = self.classification_choice.get(name)
        if classification_choice is None:
            raise KeyError(
                f"Classification choice '{name}' not found in knowledge base."
            )
        return classification_choice

    def get_classification_choice_descriptor(
        self, name: str
    ) -> "ClassificationChoiceDescriptorShallow":
        """Get a classification choice descriptor by name.

        Args:
            name (str): The name of the classification choice descriptor.
        Returns:
            ClassificationChoiceDescriptorShallow: The descriptor with the given name.
        """
        descriptor = self.classification_choice_descriptor.get(name)
        if descriptor is None:
            raise KeyError(
                f"Classification choice descriptor '{name}' not found in knowledge base."
            )
        return descriptor

    def get_examination(self, name: str) -> "ExaminationShallow":
        """Get an examination by name.

        Args:
            name (str): The name of the examination.
        Returns:
            ExaminationShallow: The examination with the given name.
        """
        examination = self.examination.get(name)
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
        examination_type = self.examination_type.get(name)
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
        intervention = self.intervention.get(name)
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
        intervention_type = self.intervention_type.get(name)
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
        indication = self.indication.get(name)
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
        indication_type = self.indication_type.get(name)
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
        information_source = self.information_source.get(name)
        if information_source is None:
            raise KeyError(f"Information source '{name}' not found in knowledge base.")
        return information_source

    @field_serializer("citation")
    def serialize_citations(
        self, citations: Dict[str, "CitationShallow"]
    ) -> Dict[str, CitationShallowDataDict]:
        r = {name: citation.to_ddict_shallow() for name, citation in citations.items()}
        return r

    @field_serializer("finding")
    def serialize_findings(
        self, findings: Dict[str, "FindingShallow"]
    ) -> Dict[str, FindingShallowDataDict]:
        r = {name: finding.to_ddict_shallow() for name, finding in findings.items()}
        return r

    @field_serializer("finding_type")
    def serialize_finding_types(
        self, finding_types: Dict[str, "FindingTypeShallow"]
    ) -> Dict[str, FindingTypeShallowDataDict]:
        r = {
            name: finding_type.to_ddict_shallow()
            for name, finding_type in finding_types.items()
        }
        return r

    @field_serializer("classification")
    def serialize_classifications(
        self, classifications: Dict[str, "ClassificationShallow"]
    ) -> Dict[str, ClassificationShallowDataDict]:
        r = {
            name: classification.to_ddict_shallow()
            for name, classification in classifications.items()
        }
        return r

    @field_serializer("classification_type")
    def serialize_classification_types(
        self, classification_types: Dict[str, "ClassificationTypeShallow"]
    ) -> Dict[str, ClassificationTypeShallowDataDict]:
        r = {
            name: classification_type.to_ddict_shallow()
            for name, classification_type in classification_types.items()
        }
        return r

    @field_serializer("classification_choice")
    def serialize_classification_choices(
        self, classification_choices: Dict[str, "ClassificationChoiceShallow"]
    ) -> Dict[str, ClassificationChoiceShallowDataDict]:
        r = {
            name: classification_choice.to_ddict_shallow()
            for name, classification_choice in classification_choices.items()
        }
        return r

    @field_serializer("classification_choice_descriptor")
    def serialize_classification_choice_descriptors(
        self,
        classification_choice_descriptors: Dict[
            str, "ClassificationChoiceDescriptorShallow"
        ],
    ) -> Dict[str, ClassificationChoiceDescriptorShallowDataDict]:
        r = {
            name: descriptor.to_ddict_shallow()
            for name, descriptor in classification_choice_descriptors.items()
        }
        return r

    @field_serializer("examination")
    def serialize_examinations(
        self, examinations: Dict[str, "ExaminationShallow"]
    ) -> Dict[str, ExaminationShallowDataDict]:
        r = {
            name: examination.to_ddict_shallow()
            for name, examination in examinations.items()
        }
        return r

    @field_serializer("examination_type")
    def serialize_examination_types(
        self, examination_types: Dict[str, "ExaminationTypeShallow"]
    ) -> Dict[str, ExaminationTypeShallowDataDict]:
        r = {
            name: examination_type.to_ddict_shallow()
            for name, examination_type in examination_types.items()
        }
        return r

    @field_serializer("intervention")
    def serialize_interventions(
        self, interventions: Dict[str, "InterventionShallow"]
    ) -> Dict[str, InterventionShallowDataDict]:
        r = {
            name: intervention.to_ddict_shallow()
            for name, intervention in interventions.items()
        }
        return r

    @field_serializer("intervention_type")
    def serialize_intervention_types(
        self, intervention_types: Dict[str, "InterventionTypeShallow"]
    ) -> Dict[str, InterventionTypeShallowDataDict]:
        r = {
            name: intervention_type.to_ddict_shallow()
            for name, intervention_type in intervention_types.items()
        }
        return r

    @field_serializer("indication")
    def serialize_indications(
        self, indications: Dict[str, "IndicationShallow"]
    ) -> Dict[str, IndicationShallowDataDict]:
        r = {
            name: indication.to_ddict_shallow()
            for name, indication in indications.items()
        }
        return r

    @field_serializer("indication_type")
    def serialize_indication_types(
        self, indication_types: Dict[str, "IndicationTypeShallow"]
    ) -> Dict[str, IndicationTypeShallowDataDict]:
        r = {
            name: indication_type.to_ddict_shallow()
            for name, indication_type in indication_types.items()
        }
        return r

    @field_serializer("information_source")
    def serialize_information_sources(
        self, information_sources: Dict[str, "InformationSourceShallow"]
    ) -> Dict[str, InformationSourceShallowDataDict]:
        r = {
            name: information_source.to_ddict_shallow()
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

    @field_serializer("unit")
    def serialize_units(
        self, units: Dict[str, "UnitShallow"]
    ) -> Dict[str, UnitShallowDataDict]:
        r = {name: unit.to_ddict_shallow() for name, unit in units.items()}
        return r

    @field_serializer("unit_type")
    def serialize_unit_types(
        self, unit_types: Dict[str, "UnitTypeShallow"]
    ) -> Dict[str, UnitTypeShallowDataDict]:
        r = {
            name: unit_type.to_ddict_shallow() for name, unit_type in unit_types.items()
        }
        return r

    def export_record_lists(self) -> KnowledgeBaseRecordLists:
        citation_records = [r.to_ddict_shallow() for r in self.citation.values()]
        finding_records = [r.to_ddict_shallow() for r in self.finding.values()]
        finding_type_records = [
            r.to_ddict_shallow() for r in self.finding_type.values()
        ]
        classification_records = [
            r.to_ddict_shallow() for r in self.classification.values()
        ]
        classification_type_records = [
            r.to_ddict_shallow() for r in self.classification_type.values()
        ]
        classification_choice_records = [
            r.to_ddict_shallow() for r in self.classification_choice.values()
        ]
        classification_choice_descriptor_records = [
            r.to_ddict_shallow() for r in self.classification_choice_descriptor.values()
        ]
        examination_records = [r.to_ddict_shallow() for r in self.examination.values()]
        examination_type_records = [
            r.to_ddict_shallow() for r in self.examination_type.values()
        ]
        indication_records = [r.to_ddict_shallow() for r in self.indication.values()]
        indication_type_records = [
            r.to_ddict_shallow() for r in self.indication_type.values()
        ]
        intervention_records = [
            r.to_ddict_shallow() for r in self.intervention.values()
        ]
        intervention_type_records = [
            r.to_ddict_shallow() for r in self.intervention_type.values()
        ]
        information_source_records = [
            r.to_ddict_shallow() for r in self.information_source.values()
        ]
        unit_records = [r.to_ddict_shallow() for r in self.unit.values()]
        unit_type_records = [r.to_ddict_shallow() for r in self.unit_type.values()]

        record_lists = KnowledgeBaseRecordLists(
            citations=citation_records,
            findings=finding_records,
            finding_types=finding_type_records,
            classifications=classification_records,
            classification_types=classification_type_records,
            classification_choices=classification_choice_records,
            classification_choice_descriptors=classification_choice_descriptor_records,
            examinations=examination_records,
            examination_types=examination_type_records,
            indications=indication_records,
            indication_types=indication_type_records,
            interventions=intervention_records,
            intervention_types=intervention_type_records,
            information_sources=information_source_records,
            units=unit_records,
            unit_types=unit_type_records,
        )

        return record_lists

    def kb_entries_by_module_name(
        self,
    ) -> Dict[str, List[Tuple[str, "KB_SHALLOW_UNION_PYDANTIC_LIST"]]]:
        """Get knowledge base entries (Shallow Models) organized by their module names."""

        export_attrs = [
            "citation",
            "finding",
            "finding_type",
            "classification",
            "classification_type",
            "classification_choice",
            "classification_choice_descriptor",
            "examination",
            "examination_type",
            "indication",
            "indication_type",
            "intervention",
            "intervention_type",
            "information_source",
            "unit",
            "unit_type",
        ]

        cfg = self.config_safe
        module_names = cfg.modules
        entries_by_module: Dict[
            str, List[Tuple[str, "KB_SHALLOW_UNION_PYDANTIC_LIST"]]
        ] = {module_name: [] for module_name in module_names}
        entries_by_module[str_unknown_factory()] = []

        for attr in export_attrs:
            kb_dict: Dict[str, "KB_SHALLOW_UNION_PYDANTIC_LIST"] = getattr(self, attr)
            kb_entry_list: List["KB_SHALLOW_UNION_PYDANTIC_LIST"] = list(
                kb_dict.values()
            )
            assert isinstance(kb_entry_list, list)
            for entry in kb_entry_list:
                module_name = entry.kb_module_name
                if module_name not in entries_by_module:
                    raise KeyError(
                        f"Module name '{module_name}' not found in knowledge base config."
                    )
                entries_by_module[module_name].append((attr, entry))

        return entries_by_module
