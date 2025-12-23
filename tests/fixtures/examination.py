from lx_dtypes.lx_django.models.core.examination import (
    Examination as DjangoExaminationModel,
)
from lx_dtypes.lx_django.models.core.examination import (
    ExaminationType as DjangoExaminationTypeModel,
)
from lx_dtypes.lx_django.models.core.finding import (
    Finding as DjangoFindingModel,
)
from lx_dtypes.lx_django.models.core.indication import (
    Indication as DjangoIndicationModel,
)
from pytest import fixture

from lx_dtypes.models.core.examination import Examination, ExaminationType
from lx_dtypes.models.core.finding import Finding
from lx_dtypes.models.core.indication import Indication


@fixture
def sample_examination_type() -> ExaminationType:
    return ExaminationType(
        uuid="123e4567-e89b-12d3-a456-426614174000",
        name="endoscopy",
        tags=["sample", "test"],
    )


@fixture(scope="function")
def sample_django_examination_type(
    sample_examination_type: ExaminationType,
) -> DjangoExaminationTypeModel:
    ddict = sample_examination_type.to_ddict_shallow()
    django_examination_type = DjangoExaminationTypeModel.sync_from_ddict_shallow(ddict)

    django_examination_type.refresh_from_db()
    return django_examination_type


@fixture
def sample_examination(
    sample_examination_type: ExaminationType,
    sample_finding: Finding,
    sample_indication: Indication,
) -> Examination:
    examination = Examination(
        uuid="123e4567-e89b-12d3-a456-426614174001",
        name="Sample Examination",
        tags=["sample", "test"],
    )
    examination.types[sample_examination_type.name] = sample_examination_type
    examination.findings[sample_finding.name] = sample_finding
    examination.indications[sample_indication.name] = sample_indication
    return examination


@fixture(scope="function")
def sample_django_examination(
    sample_examination: Examination,
    sample_django_examination_type: DjangoExaminationTypeModel,
    sample_django_finding: DjangoFindingModel,
    sample_django_indication: DjangoIndicationModel,
) -> DjangoExaminationModel:
    ddict = sample_examination.to_ddict_shallow()
    django_examination = DjangoExaminationModel.sync_from_ddict_shallow(ddict)

    django_examination.refresh_from_db()
    return django_examination
