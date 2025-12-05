from pathlib import Path

from pytest import fixture

from lx_dtypes.models.knowledge_base import DataLoader
from lx_dtypes.utils.logging import LogScope, ScopedLogWriter, get_logger

LOG_DIR = Path("./lx_dtypes/data/logs/")
YAML_REPOSITORY_DIRS = [
    Path("./lx_dtypes/data/"),
]

SAMPLE_KNOWLEDGE_BASE_NAME = "lx_knowledge_base"


@fixture(scope="session")
def demo_kb_config_name() -> str:
    return SAMPLE_KNOWLEDGE_BASE_NAME


@fixture(scope="session")
def yaml_data_loader():
    loader = DataLoader(input_dirs=YAML_REPOSITORY_DIRS)
    loader.load_module_configs()
    return loader


@fixture
def empty_data_loader() -> DataLoader:
    return DataLoader(input_dirs=[])


@fixture(scope="session")
def logger() -> ScopedLogWriter:
    scoped_logger = get_logger(
        scope=LogScope.TESTS,
        root_dir=LOG_DIR,
        output_format="yaml",
    )
    return scoped_logger


@fixture(scope="session")
def yaml_repo_dirs() -> list[Path]:
    return YAML_REPOSITORY_DIRS


@fixture(scope="session")
def uninitialized_demo_kb_config(yaml_data_loader: DataLoader, demo_kb_config_name: str):
    kb_config = yaml_data_loader.module_configs.get(demo_kb_config_name)
    assert kb_config is not None
    return kb_config


@fixture(scope="session")
def initialized_demo_kb_config(yaml_data_loader: DataLoader, demo_kb_config_name: str):
    kb_config = yaml_data_loader.get_initialized_config(demo_kb_config_name)

    return kb_config
