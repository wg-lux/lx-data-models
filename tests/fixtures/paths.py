from pathlib import Path

from pytest import fixture

LOG_DIR = Path("./lx_dtypes/data/logs/")
YAML_REPOSITORY_DIRS = [
    Path("./lx_dtypes/data/"),
]

SAMPLE_KNOWLEDGE_BASE_NAME = "lx_knowledge_base"


@fixture(scope="session")
def yaml_repo_dirs() -> list[Path]:
    return YAML_REPOSITORY_DIRS


@fixture(scope="session")
def log_dir() -> Path:
    return LOG_DIR


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
    return Path("./lx_dtypes/data/terminology/lx_interventions/data/00_generic_endoscopy_ablation.yaml")


@fixture(scope="session")
def sample_findings_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_findings/data/02_colonoscopy_observation.yaml")


@fixture(scope="session")
def sample_classifications_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_classifications/data/02_colonoscopy_polyp.yaml")


@fixture(scope="session")
def sample_classification_choices_yaml_filepath():
    return Path("./lx_dtypes/data/terminology/lx_classification_choices/data/02_colonoscopy_polyp_morphology.yaml")
