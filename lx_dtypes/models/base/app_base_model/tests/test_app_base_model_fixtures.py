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
        """
        Verify that the AppBaseModel UUID-tags data-dict fixture is provided.
        
        Parameters:
            app_base_model_uuid_tags_data_dict_fixture (AppBaseModelUUIDTagsDataDict): Fixture supplying a data dictionary for an AppBaseModel that includes UUID tags; must not be None.
        """
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
        """
        Asserts that the provided names+UUID tags pydantic fixture is an AppBaseModel instance.
        
        Parameters:
            app_base_model_names_uuid_tags_pydantic_fixture (AppBaseModel): Pytest fixture supplying an AppBaseModel populated with name and UUID tag fields.
        """
        assert isinstance(app_base_model_names_uuid_tags_pydantic_fixture, AppBaseModel)