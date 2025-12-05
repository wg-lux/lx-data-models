from lx_dtypes.utils.factories.field_defaults import (
    classification_by_name_factory,
    classification_type_by_name_factory,
    finding_type_by_name_factory,
    indication_by_name_factory,
    indication_type_by_name_factory,
    list_of_str_factory,
)


class TestDefaultFactories:
    def test_list_of_str_factory(self):
        result = list_of_str_factory()
        assert isinstance(result, list)
        assert result == []

    def test_classification_by_name_factory(self):
        result = classification_by_name_factory()
        assert isinstance(result, dict)
        assert result == {}

    def test_classification_type_by_name_factory(self):
        result = classification_type_by_name_factory()
        assert isinstance(result, dict)
        assert result == {}

    def test_finding_type_by_name_factory(self):
        result = finding_type_by_name_factory()
        assert isinstance(result, dict)
        assert result == {}

    def test_indication_by_name_factory(self):
        result = indication_by_name_factory()
        assert isinstance(result, dict)
        assert result == {}

    def test_indication_type_by_name_factory(self):
        result = indication_type_by_name_factory()
        assert isinstance(result, dict)
        assert result == {}
