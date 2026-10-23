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
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import (
    AppBaseModel,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelNamesUUIDTags import (
    AppBaseModelNamesUUIDTags,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)

TEST_UUID_STR = "123e4567-e89b-12d3-a456-426614174000"
TEST_TAG_LIST = ["tag1", "tag2"]


################# DDICTS ##################
@fixture(scope="session")
def app_base_model_data_dict_fixture() -> AppBaseModelDataDict:
    """
    Create an AppBaseModelDataDict initialized with its default values.

    Returns:
        AppBaseModelDataDict: An instance of AppBaseModelDataDict populated with the model's default field values.
    """
    ddict = AppBaseModelDataDict()
    return ddict


@fixture(scope="session")
def app_base_model_uuid_tags_data_dict_fixture() -> AppBaseModelUUIDTagsDataDict:
    """
    Create an AppBaseModelUUIDTagsDataDict populated with the test UUID and tag list.

    Returns:
        AppBaseModelUUIDTagsDataDict: A data dictionary with `uuid` set to TEST_UUID_STR and `tags` set to TEST_TAG_LIST.
    """
    ddict = AppBaseModelUUIDTagsDataDict(uuid=TEST_UUID_STR, tags=TEST_TAG_LIST)
    return ddict


@fixture(scope="session")
def app_base_model_names_uuid_tags_data_dict_fixture() -> (
    AppBaseModelNamesUUIDTagsDataDict
):
    """
    Create an AppBaseModelNamesUUIDTagsDataDict populated with sample multilingual names, description, UUID, and tags for testing.

    Returns:
        AppBaseModelNamesUUIDTagsDataDict: Instance with `name`="Sample Name", `name_de`="Beispielname", `name_en`="Sample Name EN", `description`="This is a sample description.", `uuid`=TEST_UUID_STR, and `tags`=TEST_TAG_LIST.
    """
    ddict = AppBaseModelNamesUUIDTagsDataDict(
        name="Sample Name",
        name_de="Beispielname",
        name_en="Sample Name EN",
        description="This is a sample description.",
        uuid=TEST_UUID_STR,
        tags=TEST_TAG_LIST,
    )
    return ddict


######## PYDANTIC MODELS ##########
@fixture(scope="session")
def app_base_model_pydantic_fixture(
    app_base_model_data_dict_fixture: AppBaseModelDataDict,
) -> AppBaseModel:
    """
    Create a validated AppBaseModel instance from the provided test data dictionary.

    Parameters:
        app_base_model_data_dict_fixture (AppBaseModelDataDict): Test data dictionary used to construct and validate the model.

    Returns:
        AppBaseModel: An AppBaseModel instance produced by validating the input data dictionary.
    """
    model = AppBaseModel.model_validate(app_base_model_data_dict_fixture)
    return model


@fixture(scope="session")
def app_base_model_uuid_tags_pydantic_fixture(
    app_base_model_uuid_tags_data_dict_fixture: AppBaseModelUUIDTagsDataDict,
) -> AppBaseModelUUIDTags:
    """
    Create an AppBaseModelUUIDTags instance by validating the provided data dictionary.

    Parameters:
        app_base_model_uuid_tags_data_dict_fixture (AppBaseModelUUIDTagsDataDict): Data dict containing `uuid` and `tags` used to construct and validate the pydantic model.

    Returns:
        model (AppBaseModelUUIDTags): Validated AppBaseModelUUIDTags instance.
    """
    model = AppBaseModelUUIDTags.model_validate(
        app_base_model_uuid_tags_data_dict_fixture
    )
    return model


@fixture(scope="session")
def app_base_model_names_uuid_tags_pydantic_fixture(
    app_base_model_names_uuid_tags_data_dict_fixture: AppBaseModelNamesUUIDTagsDataDict,
) -> AppBaseModelNamesUUIDTags:
    """
    Validate an AppBaseModelNamesUUIDTags data dictionary and produce an AppBaseModelNamesUUIDTags instance.

    Parameters:
        app_base_model_names_uuid_tags_data_dict_fixture (AppBaseModelNamesUUIDTagsDataDict): Data dictionary containing multilingual name fields, description, uuid, and tags to validate into the model.

    Returns:
        AppBaseModelNamesUUIDTags: The validated and instantiated model populated from the provided data dictionary.
    """
    model = AppBaseModelNamesUUIDTags.model_validate(
        app_base_model_names_uuid_tags_data_dict_fixture
    )
    return model
