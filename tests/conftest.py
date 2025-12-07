from pathlib import Path
from typing import Callable

from pytest import FixtureRequest, fixture

from lx_dtypes.models.base_models.log import Log
from lx_dtypes.models.knowledge_base import DataLoader
from lx_dtypes.utils.logging import LogLevel, LogScope, ScopedLogWriter, get_logger

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


@fixture
def log_writer(logger: ScopedLogWriter, request: FixtureRequest) -> Callable[..., Log]:
    nodeid = request.node.nodeid  # type: ignore[attr-defined]
    request_cls = request.cls  # type: ignore[attr-defined]
    if request_cls is not None:
        test_class = request_cls.__name__  # type: ignore[attr-defined]
        assert isinstance(test_class, str)
    else:
        test_class = None
    test_name = request.function.__name__

    if not isinstance(nodeid, str):  # pytest guarantees str but mypy does not
        raise TypeError("pytest nodeid must be a string")

    base_context: dict[str, str] = {
        "test": nodeid,
        "test_name": test_name,
    }

    def emit(
        message: str,
        *,
        level: LogLevel = LogLevel.INFO,
        context: dict[str, str] | None = None,
    ) -> Log:
        merged = {**base_context, **(context or {})}
        return logger.log(message, level=level, context=merged)

    return emit


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


@fixture(scope="session")
def sample_information_source_yaml_filepath():
    return Path("./lx_dtypes/data/information_source_data/data/unknown.yaml")


@fixture(scope="session")
def sample_citations_yaml_filepath():
    return Path("./lx_dtypes/data/citations/data/sample_references.yaml")


@fixture(scope="session")
def sample_examinations_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_examinations/data/colonoscopy.yaml")


@fixture(scope="session")
def sample_examination_types_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_examinations/data/examination_types.yaml")


@fixture(scope="session")
def sample_indications_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_indications/data/colonoscopy_indications.yaml")


@fixture(scope="session")
def sample_interventions_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_interventions/00_generic_endoscopy_ablation.yaml")


@fixture(scope="session")
def sample_findings_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_findings/data/02_colonoscopy_observation.yaml")


@fixture(scope="session")
def sample_classifications_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_classifications/data/02_colonoscopy_polyp.yaml")


@fixture(scope="session")
def sample_classification_choices_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_classification_choices/data/02_colonoscopy_polyp_morphology.yaml")
