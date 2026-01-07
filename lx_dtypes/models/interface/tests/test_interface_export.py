from pathlib import Path

from ..DbInterface import DbInterface

TEST_INTERFACE_EXPORT_FILE = Path("./test_interface_export.yaml")


class TestKnowledgeBaseDataLoader:
    def test_knowledge_base_data_loader(self) -> None:
        # TODO
        return None


class TestDbInterfaceExport:
    def test_db_interface_export(self, db_interface_fixture: "DbInterface") -> None:
        expected_dict = db_interface_fixture.model_dump()

        new_db_interface_instance = DbInterface.model_validate(expected_dict)
        new_dict = new_db_interface_instance.model_dump()

        # Test Dump
        new_db_interface_instance.to_yaml(TEST_INTERFACE_EXPORT_FILE)

        assert new_dict == expected_dict
