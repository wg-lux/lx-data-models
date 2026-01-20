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
    loader = DataLoader(input_dirs=yaml_repo_dirs)
    loader.load_module_configs()
    return loader


@fixture(scope="session")
def star_ugi_initialized_kb_config(
    star_ugi_yaml_data_loader: DataLoader,
) -> "KnowledgeBaseConfig":
    kb_config = star_ugi_yaml_data_loader.get_initialized_config("star_upper_gi")
    return kb_config


@fixture(scope="session")
def star_ugi_knowledge_base(star_ugi_yaml_data_loader: DataLoader) -> KnowledgeBase:
    kb = star_ugi_yaml_data_loader.load_knowledge_base("star_upper_gi")

    return kb
