from pytest import fixture

from lx_dtypes.models.ledger.center import Center


@fixture(scope="session")
def sample_center() -> Center:
    center = Center(
        name="Sample Center",
    )

    return center


@fixture(scope="session")
def sample_center_with_examiners() -> Center:
    from lx_dtypes.models.ledger.examiner import Examiner

    center = Center(
        name="Sample Center with Examiners",
    )

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
