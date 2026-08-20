from tests.fixtures.lx_dtypes.models.base.app_base_model import (
    app_base_model_data_dict_fixture,
    app_base_model_names_uuid_tags_data_dict_fixture,
    app_base_model_names_uuid_tags_pydantic_fixture,
    app_base_model_pydantic_fixture,
    app_base_model_uuid_tags_data_dict_fixture,
    app_base_model_uuid_tags_pydantic_fixture,
)
from tests.fixtures.lx_dtypes.models.interface import (
    db_interface_fixture,
    knowledge_base_fixture,
    ledger_fixture,
    lx_knowledge_base,
)
from tests.fixtures.lx_dtypes.models.interface.dataloader import (
    empty_data_loader,
    initialized_demo_kb_config,
    uninitialized_demo_kb_config,
    yaml_data_loader,
)
from tests.fixtures.lx_dtypes.models.interface.names import demo_kb_config_name
from tests.fixtures.lx_dtypes.models.interface.paths import (
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
from tests.fixtures.lx_dtypes.models.interface.star_upper_gi.dataloader import (
    star_ugi_initialized_kb_config,
    star_ugi_knowledge_base,
    star_ugi_yaml_data_loader,
)
from tests.fixtures.lx_dtypes.models.knowledge_base.citation import (
    citation_fixture,
    django_citation_fixture,
)
from tests.fixtures.lx_dtypes.models.knowledge_base.classification import (
    classification_fixture,
    classification_type_fixture,
    django_classification_fixture,
    django_classification_type_fixture,
)
from tests.fixtures.lx_dtypes.models.knowledge_base.classification_choice import (
    classification_choice_fixture,
    django_classification_choice_fixture,
)
from tests.fixtures.lx_dtypes.models.knowledge_base.classification_choice_descriptor import (
    classification_choice_descriptor_fixture,
    django_classification_choice_descriptor_fixture,
)
from tests.fixtures.lx_dtypes.models.knowledge_base.examination import (
    django_examination_fixture,
    django_examination_type_fixture,
    examination_fixture,
    examination_type_fixture,
)
from tests.fixtures.lx_dtypes.models.knowledge_base.finding import (
    django_finding_fixture,
    django_finding_type_fixture,
    finding_fixture,
    finding_type_fixture,
)
from tests.fixtures.lx_dtypes.models.knowledge_base.indication import (
    django_indication_fixture,
    django_indication_type_fixture,
    indication_fixture,
    indication_type_fixture,
)
from tests.fixtures.lx_dtypes.models.knowledge_base.intervention import (
    django_intervention_fixture,
    django_intervention_type_fixture,
    intervention_fixture,
    intervention_type_fixture,
)
from tests.fixtures.lx_dtypes.models.knowledge_base.unit import (
    django_unit_fixture,
    django_unit_type_fixture,
    unit_fixture,
    unit_type_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.center import (
    center_fixture,
    django_center_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_examination import (
    django_p_examination_fixture,
    django_populated_p_examination_fixture,
    p_examination_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_finding import (
    django_p_finding_fixture,
    django_populated_p_finding_fixture,
    p_finding_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_finding_classification_choice import (
    django_p_finding_classification_choice_fixture,
    django_populated_p_finding_classification_choice_fixture,
    p_finding_classification_choice_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_finding_classification_choice_descriptor import (
    django_p_finding_classification_choice_descriptor_fixture,
    p_finding_classification_choice_descriptor_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_finding_classifications import (
    django_p_finding_classifications_fixture,
    django_populated_p_finding_classifications_fixture,
    p_finding_classifications_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_indication import (
    django_p_indication_fixture,
    p_indication_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_indication_classification import (
    django_p_indication_classification_fixture,
    django_populated_p_indication_classification_fixture,
    p_indication_classification_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_indication_classification_descriptor import (
    django_p_indication_classification_descriptor_fixture,
    p_indication_classification_descriptor_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_intervention import (
    django_p_finding_intervention_fixture,
    p_finding_intervention_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_interventions import (
    django_p_finding_interventions_fixture,
    django_populated_p_finding_interventions_fixture,
    p_finding_interventions_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.p_video import (
    patient_video_file_data_dict_fixture,
    patient_video_file_fixture,
    raw_video_file_path,
)
from tests.fixtures.lx_dtypes.models.ledger.p_video_segment import (
    p_video_segment_data_dict_fixture,
    p_video_segment_fixture,
)
from tests.fixtures.lx_dtypes.models.ledger.patient import (
    django_patient_fixture,
    patient_fixture,
)

__all__ = [
    # App Base Model Fixtures
    "app_base_model_data_dict_fixture",
    "app_base_model_uuid_tags_data_dict_fixture",
    "app_base_model_names_uuid_tags_data_dict_fixture",
    "app_base_model_pydantic_fixture",
    "app_base_model_uuid_tags_pydantic_fixture",
    "app_base_model_names_uuid_tags_pydantic_fixture",
    # Citation Fixtures
    "citation_fixture",
    "django_citation_fixture",
    # Classification Fixtures
    "classification_fixture",
    "classification_type_fixture",
    "django_classification_fixture",
    "django_classification_type_fixture",
    # Classification Choice Fixtures
    "classification_choice_fixture",
    "django_classification_choice_fixture",
    # Classification Choice Descriptor Fixtures
    "classification_choice_descriptor_fixture",
    "django_classification_choice_descriptor_fixture",
    # Examination Fixtures
    "examination_fixture",
    "examination_type_fixture",
    "django_examination_fixture",
    "django_examination_type_fixture",
    # Finding Fixtures
    "finding_fixture",
    "finding_type_fixture",
    "django_finding_fixture",
    "django_finding_type_fixture",
    # Indication Fixtures
    "indication_fixture",
    "indication_type_fixture",
    "django_indication_fixture",
    "django_indication_type_fixture",
    # Intervention Fixtures
    "intervention_fixture",
    "intervention_type_fixture",
    "django_intervention_fixture",
    "django_intervention_type_fixture",
    # Unit Fixtures
    "unit_type_fixture",
    "unit_fixture",
    "django_unit_type_fixture",
    "django_unit_fixture",
    # db Interface Fixtures
    "db_interface_fixture",
    "knowledge_base_fixture",
    "ledger_fixture",
    # Path Fixtures
    "yaml_repo_dirs",
    "log_dir",
    "sample_citations_yaml_filepath",
    "sample_classifications_yaml_filepath",
    "sample_classification_choices_yaml_filepath",
    "sample_examinations_yaml_filepath",
    "sample_examination_types_yaml_filepath",
    "sample_findings_yaml_filepath",
    "sample_indications_yaml_filepath",
    "sample_interventions_yaml_filepath",
    "sample_information_source_yaml_filepath",
    # Names
    "demo_kb_config_name",
    # YAML Dataloader
    "empty_data_loader",
    "initialized_demo_kb_config",
    "uninitialized_demo_kb_config",
    "yaml_data_loader",
    # lx Knowledge Base Fixtures
    "lx_knowledge_base",
    ########### Ledger Fixtures ###########
    "center_fixture",
    "django_center_fixture",
    # Patient Examination Fixtures
    "p_examination_fixture",
    "django_p_examination_fixture",
    "django_populated_p_examination_fixture",
    # Patient Finding Fixtures
    "p_finding_fixture",
    "django_p_finding_fixture",
    "django_populated_p_finding_fixture",
    # Patient Indication Fixtures
    "p_indication_fixture",
    "django_p_indication_fixture",
    "p_indication_classification_fixture",
    "django_p_indication_classification_fixture",
    "django_populated_p_indication_classification_fixture",
    "p_indication_classification_descriptor_fixture",
    "django_p_indication_classification_descriptor_fixture",
    # Patient Interventions fixtures
    "p_finding_interventions_fixture",
    "django_p_finding_interventions_fixture",
    "django_populated_p_finding_interventions_fixture",
    # Patient Finding Intervention Fixtures
    "p_finding_intervention_fixture",
    "django_p_finding_intervention_fixture",
    # Patient Finding Classifications Fixtures
    "p_finding_classifications_fixture",
    "django_p_finding_classifications_fixture",
    "django_populated_p_finding_classifications_fixture",
    # Patient Finding Classification Choice Fixtures
    "p_finding_classification_choice_fixture",
    "django_p_finding_classification_choice_fixture",
    "django_populated_p_finding_classification_choice_fixture",
    # Patient Finding Classification Choice Descriptor Fixtures
    "p_finding_classification_choice_descriptor_fixture",
    "django_p_finding_classification_choice_descriptor_fixture",
    # Patient Fixtures
    "patient_fixture",
    "django_patient_fixture",
    # Video Base Model Fixtures
    "raw_video_file_path",
    "patient_video_file_data_dict_fixture",
    "patient_video_file_fixture",
    # STAR UGI
    "star_ugi_yaml_data_loader",
    "star_ugi_initialized_kb_config",
    "star_ugi_knowledge_base",
    # Video Segment Fixtures
    "p_video_segment_data_dict_fixture",
    "p_video_segment_fixture",
]
