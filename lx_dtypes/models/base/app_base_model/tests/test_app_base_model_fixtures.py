from lx_dtypes.models.base.app_base_model.ddict import (
    AppBaseModelDataDict,
    AppBaseModelNamesUUIDTagsDataDict,
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import (
    AppBaseModel,
)


class TestAppBaseModelFixtures:
    def test_app_base_model_data_dict_fixture(
        self,
        app_base_model_data_dict_fixture: AppBaseModelDataDict,
    ) -> None:
        assert app_base_model_data_dict_fixture == {}

    def test_app_base_model_uuid_tags_data_dict_fixture(
        self,
        app_base_model_uuid_tags_data_dict_fixture: AppBaseModelUUIDTagsDataDict,
    ) -> None:
        assert app_base_model_uuid_tags_data_dict_fixture is not None

    def test_app_base_model_names_uuid_tags_data_dict_fixture(
        self,
        app_base_model_names_uuid_tags_data_dict_fixture: AppBaseModelNamesUUIDTagsDataDict,
    ) -> None:
        assert app_base_model_names_uuid_tags_data_dict_fixture is not None

    def test_app_base_model_instance_creation(
        self,
        app_base_model_pydantic_fixture: AppBaseModel,
    ) -> None:
        assert isinstance(app_base_model_pydantic_fixture, AppBaseModel)

    def test_app_base_model_uuid_tags_instance_creation(
        self,
        app_base_model_uuid_tags_pydantic_fixture: AppBaseModel,
    ) -> None:
        assert isinstance(app_base_model_uuid_tags_pydantic_fixture, AppBaseModel)

    def test_app_base_model_names_uuid_tags_instance_creation(
        self,
        app_base_model_names_uuid_tags_pydantic_fixture: AppBaseModel,
    ) -> None:
        assert isinstance(app_base_model_names_uuid_tags_pydantic_fixture, AppBaseModel)
