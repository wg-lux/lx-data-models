from pathlib import Path

from pytest import fixture

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig

YAML_REPOSITORY_DIRS = [
    Path("./lx_dtypes/data/"),
]


@fixture(scope="session")
def star_ugi_yaml_data_loader(yaml_repo_dirs: list[Path]) -> DataLoader:
    """
    Create and initialize a DataLoader configured with the given YAML repository directories.

    Parameters:
        yaml_repo_dirs (list[Path]): Paths to directories containing YAML module configurations.

    Returns:
        DataLoader: A DataLoader instance with module configurations loaded.
    """
    loader = DataLoader(input_dirs=yaml_repo_dirs)
    loader.load_module_configs()
    return loader


@fixture(scope="session")
def star_ugi_initialized_kb_config(
    star_ugi_yaml_data_loader: DataLoader,
) -> "KnowledgeBaseConfig":
    """
    Provide an initialized KnowledgeBaseConfig for the "star_upper_gi" knowledge base.

    Returns:
        KnowledgeBaseConfig: Initialized configuration for the "star_upper_gi" knowledge base.
    """
    kb_config = star_ugi_yaml_data_loader.get_initialized_config("star_upper_gi")
    return kb_config


@fixture(scope="session")
def star_ugi_knowledge_base(star_ugi_yaml_data_loader: DataLoader) -> KnowledgeBase:
    """
    Load and return the KnowledgeBase for the "star_upper_gi" dataset.

    Returns:
        KnowledgeBase: The loaded knowledge base for "star_upper_gi".
    """
    kb = star_ugi_yaml_data_loader.load_knowledge_base("star_upper_gi")

    return kb
