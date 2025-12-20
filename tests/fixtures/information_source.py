from pytest import fixture

from lx_dtypes.contrib.lx_django.models.core.information_source import (
    InformationSource as DjangoInformationSourceModel,
)
from lx_dtypes.contrib.lx_django.models.core.information_source import (
    InformationSourceType as DjangoInformationSourceTypeModel,
)
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


@fixture(scope="function")
def sample_django_information_source_type(
    sample_information_source_type: InformationSourceType,
) -> DjangoInformationSourceTypeModel:
    ddict = sample_information_source_type.to_ddict_shallow()
    django_information_source_type = (
        DjangoInformationSourceTypeModel.sync_from_ddict_shallow(ddict)
    )
    django_information_source_type.refresh_from_db()
    return django_information_source_type


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


@fixture(scope="function")
def sample_django_information_source(
    sample_information_source: InformationSource,
    sample_django_information_source_type: DjangoInformationSourceTypeModel,
) -> DjangoInformationSourceModel:
    ddict = sample_information_source.to_ddict_shallow()
    django_information_source = DjangoInformationSourceModel.sync_from_ddict_shallow(
        ddict
    )
    django_information_source.refresh_from_db()
    return django_information_source
