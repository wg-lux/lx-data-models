from pytest import fixture

from lx_dtypes.models.core.information_source import (
    InformationSource,
    InformationSourceType,
)


@fixture
def sample_information_source_type() -> InformationSourceType:
    return InformationSourceType(
        name="Test Information Source Type",
        name_de="Test Informationsquelle Typ",
        name_en="Test Information Source Type",
        description="A test information source type.",
    )


@fixture
def sample_information_source(
    sample_information_source_type: InformationSourceType,
) -> InformationSource:
    return InformationSource(
        name="Test Information Source",
        name_de="Test Informationsquelle",
        name_en="Test Information Source",
        description="A test information source.",
        types={sample_information_source_type.name: sample_information_source_type},
    )
