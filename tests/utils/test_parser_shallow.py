from pathlib import Path
from typing import Callable

from lx_dtypes.models.shallow import CitationShallow, ExaminationShallow, ExaminationTypeShallow, IndicationShallow, InformationSourceShallow
from lx_dtypes.models.shallow.intervention import InterventionShallow
from lx_dtypes.utils.logging import Log
from lx_dtypes.utils.parser import parse_shallow_object


class TestParser:
    def test_parse_information_source_shallow(self, sample_information_source_yaml_filepath: Path, log_writer: Callable[..., Log]):
        parsed_objects = [_ for _ in parse_shallow_object(sample_information_source_yaml_filepath)]

        assert len(parsed_objects) > 0
        for obj in parsed_objects:
            assert obj.source_file == sample_information_source_yaml_filepath
            assert isinstance(obj, InformationSourceShallow)

        log_writer(f"Parsed {len(parsed_objects)} InformationSourceShallow objects from {sample_information_source_yaml_filepath}")

    def test_parse_citation_shallow(self, sample_citations_yaml_filepath: Path, log_writer: Callable[..., Log]):
        parsed_objects = list(parse_shallow_object(sample_citations_yaml_filepath))
        assert len(parsed_objects) > 0
        for obj in parsed_objects:
            assert obj.source_file == sample_citations_yaml_filepath
            assert isinstance(obj, CitationShallow)

        log_writer(f"Parsed {len(parsed_objects)} CitationShallow objects from {sample_citations_yaml_filepath}")

    def test_parse_examination_shallow(self, sample_examinations_yaml_filepath: Path, log_writer: Callable[..., Log]):
        parsed_objects = list(parse_shallow_object(sample_examinations_yaml_filepath))
        assert len(parsed_objects) > 0
        for obj in parsed_objects:
            assert obj.source_file == sample_examinations_yaml_filepath
            assert isinstance(obj, ExaminationShallow)

        log_writer(f"Parsed {len(parsed_objects)} ExaminationShallow objects from {sample_examinations_yaml_filepath}")

    def test_parse_examination_type_shallow(self, sample_examination_types_yaml_filepath: Path, log_writer: Callable[..., Log]):
        parsed_objects = list(parse_shallow_object(sample_examination_types_yaml_filepath))
        assert len(parsed_objects) > 0
        for obj in parsed_objects:
            assert obj.source_file == sample_examination_types_yaml_filepath
            assert isinstance(obj, ExaminationTypeShallow)

        log_writer(f"Parsed {len(parsed_objects)} ExaminationShallow objects from {sample_examination_types_yaml_filepath}")

    def test_parse_indication_shallow(self, sample_indications_yaml_filepath: Path, log_writer: Callable[..., Log]):
        parsed_objects = list(parse_shallow_object(sample_indications_yaml_filepath))
        assert len(parsed_objects) > 0
        for obj in parsed_objects:
            assert obj.source_file == sample_indications_yaml_filepath
            assert isinstance(obj, IndicationShallow)

        log_writer(f"Parsed {len(parsed_objects)} IndicationShallow objects from {sample_indications_yaml_filepath}")

    def test_parse_intervention_shallow(self, sample_interventions_yaml_filepath: Path, log_writer: Callable[..., Log]):
        parsed_objects = list(parse_shallow_object(sample_interventions_yaml_filepath))
        assert len(parsed_objects) > 0
        for obj in parsed_objects:
            assert obj.source_file == sample_interventions_yaml_filepath
            assert isinstance(obj, InterventionShallow)

        log_writer(f"Parsed {len(parsed_objects)} InterventionShallow objects from {sample_interventions_yaml_filepath}")

    def test_parse_finding_shallow(self, sample_findings_yaml_filepath: Path, log_writer: Callable[..., Log]):
        parsed_objects = list(parse_shallow_object(sample_findings_yaml_filepath))
        assert len(parsed_objects) > 0
        for obj in parsed_objects:
            assert obj.source_file == sample_findings_yaml_filepath
            from lx_dtypes.models.shallow.finding import FindingShallow

            assert isinstance(obj, FindingShallow)

        log_writer(f"Parsed {len(parsed_objects)} FindingShallow objects from {sample_findings_yaml_filepath}")

    def test_parse_classification_shallow(self, sample_classifications_yaml_filepath: Path, log_writer: Callable[..., Log]):
        parsed_objects = list(parse_shallow_object(sample_classifications_yaml_filepath))
        assert len(parsed_objects) > 0
        for obj in parsed_objects:
            assert obj.source_file == sample_classifications_yaml_filepath
            from lx_dtypes.models.shallow.classification import ClassificationShallow

            if isinstance(obj, ClassificationShallow):
                log_writer(f"Parsed ClassificationShallow object: {obj.name}")

        log_writer(f"Parsed {len(parsed_objects)} ClassificationShallow objects from {sample_classifications_yaml_filepath}")

    def test_parse_classification_choice_shallow(self, sample_classification_choices_yaml_filepath: Path, log_writer: Callable[..., Log]):
        parsed_objects = list(parse_shallow_object(sample_classification_choices_yaml_filepath))
        assert len(parsed_objects) > 0
        for obj in parsed_objects:
            assert obj.source_file == sample_classification_choices_yaml_filepath
            from lx_dtypes.models.shallow.classification_choice import ClassificationChoiceShallow

            assert isinstance(obj, ClassificationChoiceShallow)

        log_writer(f"Parsed {len(parsed_objects)} ClassificationChoiceShallow objects from {sample_classification_choices_yaml_filepath}")
