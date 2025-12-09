from pytest import fixture


@fixture(scope="session")
def examination_name_colonoscopy() -> str:
    return "colonoscopy"


@fixture(scope="session")
def finding_name_colon_polyp() -> str:
    return "colon_polyp"
