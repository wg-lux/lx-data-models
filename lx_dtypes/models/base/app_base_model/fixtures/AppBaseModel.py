from pytest import fixture

from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelDataDict import (
    AppBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelNamesUUIDTagsDataDict import (
    AppBaseModelNamesUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)

TEST_UUID_STR = "123e4567-e89b-12d3-a456-426614174000"
TEST_TAG_LIST = ["tag1", "tag2"]


################# DDICTS ##################
@fixture(scope="session")
def app_base_model_data_dict_fixture() -> AppBaseModelDataDict:
    ddict = AppBaseModelDataDict()
    return ddict


@fixture(scope="session")
def app_base_model_uuid_tags_data_dict_fixture() -> AppBaseModelUUIDTagsDataDict:
    ddict = AppBaseModelUUIDTagsDataDict(uuid=TEST_UUID_STR, tags=TEST_TAG_LIST)
    return ddict


@fixture(scope="session")
def app_base_model_names_uuid_tags_data_dict_fixture() -> (
    AppBaseModelNamesUUIDTagsDataDict
):
    ddict = AppBaseModelNamesUUIDTagsDataDict(
        name="Sample Name",
        name_de="Beispielname",
        name_en="Sample Name EN",
        description="This is a sample description.",
        uuid=TEST_UUID_STR,
        tags=TEST_TAG_LIST,
    )
    return ddict
