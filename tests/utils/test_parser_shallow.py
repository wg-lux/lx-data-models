from pathlib import Path
from typing import Callable

from lx_dtypes.models.shallow import CitationShallow, InformationSourceShallow
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
