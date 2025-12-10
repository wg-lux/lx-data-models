from pytest import fixture


@fixture(scope="session")
def examination_name_colonoscopy() -> str:
    return "colonoscopy"


@fixture(scope="session")
def finding_name_colon_polyp() -> str:
    return "colon_polyp"


@fixture(scope="session")
def classification_name_lesion_size_mm() -> str:
    return "lesion_size_mm"


@fixture(scope="session")
def classification_name_colon_lesion_paris() -> str:
    return "colon_lesion_paris"


@fixture(scope="session")
def classification_choice_name_lesion_size_oval_mm() -> str:
    return "lesion_size_oval_mm"


@fixture(scope="session")
def classification_choice_name_paris_1s() -> str:
    return "colon_lesion_paris_Is"


@fixture(scope="session")
def indication_name_screening_colonoscopy() -> str:
    return "colonoscopy_screening"
