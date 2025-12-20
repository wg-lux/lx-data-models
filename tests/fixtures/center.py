from pytest import fixture

from lx_dtypes.models.ledger.center import Center


@fixture(scope="session")
def sample_center() -> Center:
    center = Center(
        name="Sample Center",
    )

    return center
