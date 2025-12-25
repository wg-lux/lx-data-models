from pytest import fixture

from lx_dtypes.lx_django.models.ledger.center import (
    Center as DjangoCenterModel,
)
from lx_dtypes.models.ledger.center import Center


@fixture(scope="session")
def sample_center() -> Center:
    center = Center(
        name="Sample Center",
    )

    return center


@fixture(scope="session")
def sample_center_with_examiners(sample_center: Center) -> Center:
    from lx_dtypes.models.ledger.examiner import Examiner

    center = sample_center
    examiner1 = Examiner(
        first_name="Alice",
        last_name="Smith",
        center_name=center.name,
    )

    examiner2 = Examiner(
        first_name="Bob",
        last_name="Johnson",
        center_name=center.name,
    )

    center.examiners[examiner1.uuid] = examiner1
    center.examiners[examiner2.uuid] = examiner2

    return center


@fixture(scope="function")
def sample_django_center_with_examiners(
    sample_center_with_examiners: Center,
) -> "DjangoCenterModel":
    from lx_dtypes.lx_django.models.ledger.center import Center as DjangoCenterModel

    ddict = sample_center_with_examiners.to_ddict()
    django_center = DjangoCenterModel.sync_from_ddict(ddict)

    django_center.refresh_from_db()
    return django_center
