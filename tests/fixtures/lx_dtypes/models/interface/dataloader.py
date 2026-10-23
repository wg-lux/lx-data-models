from pathlib import Path
from typing import TYPE_CHECKING

from pytest import fixture

from lx_dtypes.models.interface.DataLoader import DataLoader

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig


@fixture(scope="session")
def uninitialized_demo_kb_config(
    yaml_data_loader: DataLoader, demo_kb_config_name: str
) -> "KnowledgeBaseConfig":
    """
    Retrieve an uninitialized knowledge-base configuration by name from the given YAML data loader.

    Parameters:
        yaml_data_loader (DataLoader): Data loader containing loaded module configurations.
        demo_kb_config_name (str): Key name of the demo knowledge-base configuration to retrieve.

    Returns:
        KnowledgeBaseConfig: The requested knowledge-base configuration object.

    Raises:
        AssertionError: If no configuration with the given name exists in the data loader.
    """
    kb_config = yaml_data_loader.module_configs.get(demo_kb_config_name)
    assert kb_config is not None
    return kb_config


@fixture(scope="session")
def initialized_demo_kb_config(
    yaml_data_loader: DataLoader, demo_kb_config_name: str
) -> "KnowledgeBaseConfig":
    """
    Return an initialized knowledge base configuration by name.

    Parameters:
        yaml_data_loader (DataLoader): DataLoader instance used to load and initialize configurations.
        demo_kb_config_name (str): Name of the knowledge base configuration to initialize and return.

    Returns:
        kb_config (KnowledgeBaseConfig): The initialized knowledge base configuration corresponding to the given name.
    """
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
