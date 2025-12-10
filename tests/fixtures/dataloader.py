from pathlib import Path

from pytest import fixture

from lx_dtypes.models.knowledge_base import DataLoader


@fixture(scope="session")
def uninitialized_demo_kb_config(
    yaml_data_loader: DataLoader, demo_kb_config_name: str
):
    kb_config = yaml_data_loader.module_configs.get(demo_kb_config_name)
    assert kb_config is not None
    return kb_config


@fixture(scope="session")
def initialized_demo_kb_config(yaml_data_loader: DataLoader, demo_kb_config_name: str):
    kb_config = yaml_data_loader.get_initialized_config(demo_kb_config_name)

    return kb_config


@fixture(scope="session")
def yaml_data_loader(yaml_repo_dirs: list[Path]) -> DataLoader:
    loader = DataLoader(input_dirs=yaml_repo_dirs)
    loader.load_module_configs()
    return loader


@fixture
def empty_data_loader() -> DataLoader:
    return DataLoader(input_dirs=[])
