from pytest import fixture

from .fixtures.dataloader import (
    empty_data_loader,
    initialized_demo_kb_config,
    uninitialized_demo_kb_config,
    yaml_data_loader,
)
from .fixtures.knowledge_base import lx_knowledge_base
from .fixtures.logs import log_writer, logger
from .fixtures.object_names import (
    examination_name_colonoscopy,
    finding_name_colon_polyp,
)
from .fixtures.paths import (
    log_dir,
    sample_citations_yaml_filepath,
    sample_classification_choices_yaml_filepath,
    sample_classifications_yaml_filepath,
    sample_examination_types_yaml_filepath,
    sample_examinations_yaml_filepath,
    sample_findings_yaml_filepath,
    sample_indications_yaml_filepath,
    sample_information_source_yaml_filepath,
    sample_interventions_yaml_filepath,
    yaml_repo_dirs,
)
from .fixtures.patient import sample_patient
from .fixtures.patient_examination import (
    sample_patient_examination,
    sample_patient_finding_colon_polyp,
)
from .fixtures.patient_interface import sample_patient_interface
from .fixtures.patient_ledger import (
    sample_patient_ledger,
    sample_patient_ledger_patient_uuid,
)
from .fixtures.person import sample_person, sample_person_no_dob_no_gender

SAMPLE_KNOWLEDGE_BASE_NAME = "lx_knowledge_base"


@fixture(scope="session")
def demo_kb_config_name() -> str:
    return SAMPLE_KNOWLEDGE_BASE_NAME


__all__ = [
    "empty_data_loader",
    "initialized_demo_kb_config",
    "uninitialized_demo_kb_config",
    "yaml_data_loader",
    "lx_knowledge_base",
    "log_writer",
    "logger",
    "log_dir",
    "sample_citations_yaml_filepath",
    "sample_classification_choices_yaml_filepath",
    "sample_classifications_yaml_filepath",
    "sample_examination_types_yaml_filepath",
    "sample_examinations_yaml_filepath",
    "sample_findings_yaml_filepath",
    "sample_indications_yaml_filepath",
    "sample_information_source_yaml_filepath",
    "sample_interventions_yaml_filepath",
    "yaml_repo_dirs",
    "sample_person_no_dob_no_gender",
    "sample_person",
    "sample_patient",
    "demo_kb_config_name",
    "sample_patient_ledger",
    "sample_patient_ledger_patient_uuid",
    "sample_patient_interface",
    "examination_name_colonoscopy",
    "finding_name_colon_polyp",
    "sample_patient_examination",
    "sample_patient_finding_colon_polyp",
]
