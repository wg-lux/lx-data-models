from pytest import fixture

from .fixtures.center import sample_center
from .fixtures.citation import sample_citation
from .fixtures.classification import sample_classification, sample_classification_type
from .fixtures.classification_choice import sample_classification_choice
from .fixtures.classification_choice_descriptor import (
    sample_classification_choice_descriptor_numeric,
)
from .fixtures.dataloader import (
    empty_data_loader,
    initialized_demo_kb_config,
    uninitialized_demo_kb_config,
    yaml_data_loader,
)
from .fixtures.django import ninja_test_client
from .fixtures.examination import sample_examination, sample_examination_type
from .fixtures.examiner import sample_examiner
from .fixtures.finding import sample_finding, sample_finding_type
from .fixtures.indication import sample_indication, sample_indication_type
from .fixtures.intervention import sample_intervention, sample_intervention_type
from .fixtures.knowledge_base import lx_knowledge_base
from .fixtures.logs import log_writer, logger
from .fixtures.object_names import (
    classification_choice_name_lesion_size_oval_mm,
    classification_choice_name_paris_1s,
    classification_name_colon_lesion_paris,
    classification_name_lesion_size_mm,
    examination_name_colonoscopy,
    finding_name_colon_polyp,
    indication_name_screening_colonoscopy,
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
    sample_patient_finding_with_classification_choice,
)
from .fixtures.patient_interface import sample_patient_interface
from .fixtures.patient_ledger import (
    sample_patient_ledger,
    sample_patient_ledger_patient_uuid,
)
from .fixtures.person import sample_person, sample_person_no_dob_no_gender
from .fixtures.unit import sample_unit, sample_unit_type

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
    "classification_name_lesion_size_mm",
    "classification_choice_name_lesion_size_oval_mm",
    "classification_choice_name_paris_1s",
    "indication_name_screening_colonoscopy",
    "sample_patient_finding_with_classification_choice",
    "classification_name_colon_lesion_paris",
    "ninja_test_client",
    "sample_examiner",
    "sample_center",
    "sample_classification_choice_descriptor_numeric",
    "sample_classification_choice",
    "sample_classification_type",
    "sample_classification",
    "sample_intervention_type",
    "sample_intervention",
    "sample_unit_type",
    "sample_unit",
    "sample_finding_type",
    "sample_finding",
    "sample_indication_type",
    "sample_indication",
    "sample_examination_type",
    "sample_examination",
    "sample_citation",
]
