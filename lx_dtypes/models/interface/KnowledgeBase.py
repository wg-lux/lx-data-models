from pathlib import Path
from typing import Dict, List, Self, Tuple, TypedDict, Union, cast

import yaml
from pydantic import Field

from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
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
from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitDataDict import UnitDataDict
from lx_dtypes.models.knowledge_base.unit.UnitType import UnitType
from lx_dtypes.models.knowledge_base.unit.UnitTypeDataDict import UnitTypeDataDict
from lx_dtypes.utils.parser import camel_to_snake, parse_shallow_object, snake_to_camel


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


YAML_IMPORT_SKIP_FIELDS = ["config", "uuid", "source_file", "created_at", "updated_at"]


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

    def get_classification(self, name: str) -> Classification:
        """
        Retrieve a Classification by its name from this knowledge base.

        Parameters:
            name (str): The classification's unique name/key.

        Returns:
            Classification: The Classification instance identified by `name`.
        """
        return self.classification[name]

    def get_classification_type(self, name: str) -> ClassificationType:
        """
        Retrieve a ClassificationType by its name.

        Returns:
            The ClassificationType with the given name.
        """
        return self.classification_type[name]

    def get_classification_choice(self, name: str) -> ClassificationChoice:
        """
        Retrieve a ClassificationChoice by its registered name.

        Parameters:
            name (str): The unique name/key of the classification choice to retrieve.

        Returns:
            ClassificationChoice: The classification choice instance associated with `name`.
        """
        return self.classification_choice[name]

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
        return self.classification_choice_descriptor[name]

    def get_examination(self, name: str) -> Examination:
        """
        Retrieve an Examination by its name.

        Returns:
            Examination: The Examination instance associated with the given name.
        """
        return self.examination[name]

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
        return self.examination_type[name]

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
        return self.finding[name]

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
        return self.finding_type[name]

    def get_indication(self, name: str) -> Indication:
        """
        Retrieve an Indication by its name.

        Parameters:
            name (str): The unique name/key of the indication to retrieve.

        Returns:
            Indication: The Indication instance matching the provided name.
        """
        return self.indication[name]

    def get_indication_type(self, name: str) -> IndicationType:
        """
        Retrieve an IndicationType by its name.

        Returns:
            The IndicationType with the given name.
        """
        return self.indication_type[name]

    def get_intervention(self, name: str) -> Intervention:
        """
        Retrieve an Intervention by its name from the knowledge base.

        Parameters:
            name (str): The intervention's name (dictionary key) to look up.

        Returns:
            Intervention: The Intervention instance with the given name.
        """
        return self.intervention[name]

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
        return self.intervention_type[name]

    def get_unit_type(self, name: str) -> UnitType:
        """
        Retrieve a UnitType from the knowledge base by its name.

        Parameters:
            name (str): The name of the unit type to retrieve.

        Returns:
            UnitType: The unit type with the given name.
        """
        return self.unit_type[name]

    def get_unit(self, name: str) -> Unit:
        """
        Retrieve the Unit with the given name from the knowledge base.

        Parameters:
            name (str): The unit's identifier as stored in the knowledge base.

        Returns:
            Unit: The Unit instance corresponding to the provided name.
        """
        return self.unit[name]

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
        data = config.data
        submodule_files = data.get_files_with_suffix(".yaml")
        for sm_file in submodule_files:
            parsed_object_generator = parse_shallow_object(sm_file, kb_module_name=name)
            for parsed_object in parsed_object_generator:
                model_name = camel_to_snake(type(parsed_object).__name__)
                object_name = parsed_object.name
                if not hasattr(kb, model_name):
                    raise ValueError(f"KnowledgeBase has no attribute '{model_name}'")
                model_dict: Dict[str, KB_MODELS] = getattr(kb, model_name)
                if object_name in model_dict:
                    pass  # or raise warning?
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

        Returns:
            KnowledgeBaseRecordList: A TypedDict containing lists of data-dictionary records for each KB category with keys:
                - citations
                - classifications
                - classification_types
                - classification_choices
                - classification_choice_descriptors
                - examinations
                - examination_types
                - findings
                - finding_types
                - indications
                - indication_types
                - interventions
                - intervention_types
                - units
                - unit_types
                - information_sources
                - information_source_types
        """
        citation_records = [r.ddict for r in self.citation.values()]
        classification_records = [r.ddict for r in self.classification.values()]
        classification_type_records = [
            r.ddict for r in self.classification_type.values()
        ]
        classification_choice_records = [
            r.ddict for r in self.classification_choice.values()
        ]
        classification_choice_descriptor_records = [
            r.ddict for r in self.classification_choice_descriptor.values()
        ]
        examination_records = [r.ddict for r in self.examination.values()]
        examination_type_records = [r.ddict for r in self.examination_type.values()]
        finding_records = [r.ddict for r in self.finding.values()]
        finding_type_records = [r.ddict for r in self.finding_type.values()]
        indication_records = [r.ddict for r in self.indication.values()]
        indication_type_records = [r.ddict for r in self.indication_type.values()]
        intervention_records = [r.ddict for r in self.intervention.values()]
        intervention_type_records = [r.ddict for r in self.intervention_type.values()]
        unit_records = [r.ddict for r in self.unit.values()]
        unit_type_records = [r.ddict for r in self.unit_type.values()]
        information_source_records = [r.ddict for r in self.information_source.values()]
        information_source_type_records = [
            r.ddict for r in self.information_source_type.values()
        ]

        record_lists = KnowledgeBaseRecordList(
            citations=citation_records,
            classifications=classification_records,
            classification_types=classification_type_records,
            classification_choices=classification_choice_records,
            classification_choice_descriptors=classification_choice_descriptor_records,
            examinations=examination_records,
            examination_types=examination_type_records,
            findings=finding_records,
            finding_types=finding_type_records,
            indications=indication_records,
            indication_types=indication_type_records,
            interventions=intervention_records,
            intervention_types=intervention_type_records,
            units=unit_records,
            unit_types=unit_type_records,
            information_sources=information_source_records,
            information_source_types=information_source_type_records,
        )

        return record_lists
