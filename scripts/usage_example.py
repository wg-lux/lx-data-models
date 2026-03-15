import os
from pathlib import Path

import django

# Ensure the Django app config is loaded when this script is invoked standalone.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lx_dtypes.django_settings")
django.setup()

from lx_dtypes.models.interface.DataLoader import DataLoader  # noqa: E402
from lx_dtypes.models.interface.DbInterface import DbInterface  # noqa: E402
from lx_dtypes.models.interface.Ledger import Ledger  # noqa: E402
from lx_dtypes.utils.dataframe import interface2dataset  # noqa: E402

DATA_DIRECTORIES = [Path("./demo-data/")]
EXAMINATION_NAME = "star_upper_gi_endoscopy"
DATASET_EXPORT_DIR = Path("./standardized_dataset/")
DATASET_EXPORT_DIR.mkdir(
    exist_ok=True
)  # Create the export directory if it doesn't exist


######### DB INTERFACE SETUP ###########
# Initialize the DataLoader with the specified data directories
dataloader = DataLoader(input_dirs=DATA_DIRECTORIES)

# Scan the directories for all available config.yaml files
dataloader.load_module_configs()

# Initialize the KnowledgeBaseConfig "star_upper_gi"
kb_config = dataloader.get_initialized_config("star_upper_gi")

# Retrieve the KnowledgeBase "star_upper_gi"
kb = dataloader.load_knowledge_base("star_upper_gi")

# Export the KnowledgeBase as .yaml object
kb.to_yaml(Path("./star_upper_gi_kb_export_test.yaml"))

# Create an empty ledger
ledger = Ledger()

# Initialize the DbInterface object
db_interface = DbInterface(
    knowledge_base=kb,
    ledger=ledger,
)


###### CREATE EXAMPLE PATIENT AND EXAMINATIONS ######
# Import Helpers to create example findings with classifications for demonstration purposes
# To see them, check the source code of lx_dtypes.models.interface.tests.test_star_upper_gi on GitHub
from lx_dtypes.models.interface.tests.test_star_upper_gi import (  # noqa: E402
    FINDINGS_ABNORMAL,
    FINDINGS_ABNORMAL_W_DESCRIPTORS,
    FINDINGS_NORMAL,
    FINDINGS_NORMAL_W_DESCRIPTORS,
)

# Create a patient and an examination for that patient, so we can demonstrate how to create segments linked to that examination
patient = db_interface.create_patient(
    first_name="John",
    last_name="Doe",
    dob="1980-01-01",
)

p_examination = db_interface.create_patient_examination(
    patient=patient,
    examination=EXAMINATION_NAME,
)

## create normal findings
for finding_name, classification_choice_tuples in FINDINGS_NORMAL:
    p_finding = db_interface.create_examination_finding(
        patient_examination=p_examination,
        finding=finding_name,
    )
    for (
        classification_name,
        classification_choice_name,
    ) in classification_choice_tuples:
        db_interface.create_patient_finding_classification_choice(
            patient_examination=p_examination,
            patient_finding=p_finding,
            classification=classification_name,
            classification_choice=classification_choice_name,
        )
# create normal findings with descriptors
for finding_name, classification_choice_tuples in FINDINGS_NORMAL_W_DESCRIPTORS:  # type: ignore # TODO fix typing
    p_finding = db_interface.create_examination_finding(
        patient_examination=p_examination,
        finding=finding_name,
    )
    for (
        classification_name,
        classification_choice_name,
        descriptor_name,
        descriptor_value,
    ) in classification_choice_tuples:
        p_classification_choice = (
            db_interface.create_patient_finding_classification_choice(
                patient_examination=p_examination,
                patient_finding=p_finding,
                classification=classification_name,
                classification_choice=classification_choice_name,
            )
        )
        if not descriptor_name:
            continue
        descriptor = db_interface.knowledge_base.get_classification_choice_descriptor(
            name=descriptor_name
        )
        p_classification_choice.create_descriptor(
            descriptor=descriptor,
            descriptor_value=descriptor_value,
        )

# Create second examination with abnormal findings
p_examination_abnormal = db_interface.create_patient_examination(
    patient=patient,
    examination=EXAMINATION_NAME,
)

for finding_name, classification_choice_tuples in FINDINGS_ABNORMAL:
    p_finding = db_interface.create_examination_finding(
        patient_examination=p_examination_abnormal,
        finding=finding_name,
    )
    for (
        classification_name,
        classification_choice_name,
    ) in classification_choice_tuples:
        db_interface.create_patient_finding_classification_choice(
            patient_examination=p_examination_abnormal,
            patient_finding=p_finding,
            classification=classification_name,
            classification_choice=classification_choice_name,
        )

for (
    finding_name,
    classification_choice_tuples,
) in FINDINGS_ABNORMAL_W_DESCRIPTORS:
    p_finding = db_interface.create_examination_finding(
        patient_examination=p_examination_abnormal,
        finding=finding_name,
    )
    for (  # type: ignore # TODO fix typing
        classification_name,
        classification_choice_name,
        descriptor_name,
        descriptor_value,
    ) in classification_choice_tuples:
        p_classification_choice = (
            db_interface.create_patient_finding_classification_choice(
                patient_examination=p_examination_abnormal,
                patient_finding=p_finding,
                classification=classification_name,
                classification_choice=classification_choice_name,
            )
        )
        if not descriptor_name:
            continue
        descriptor = db_interface.knowledge_base.get_classification_choice_descriptor(
            name=descriptor_name
        )
        p_classification_choice.create_descriptor(
            descriptor=descriptor,
            descriptor_value=descriptor_value,
        )

# EXPERIMENTAL: Export CSV Files
# Will currently throw UserWarnings for empty dataframes
dataset = interface2dataset(db_interface)
dataset.to_csvs(DATASET_EXPORT_DIR)

db_interface.to_yaml(Path("./star_upper_gi_interface_export_test.yaml"))
