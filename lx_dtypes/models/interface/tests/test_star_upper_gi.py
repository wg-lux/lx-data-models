from datetime import date
from pathlib import Path

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.DbInterface import DbInterface
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.interface.Ledger import Ledger
from lx_dtypes.utils.dataframe import interface2dataset

DATASET_EXPORT_DIR = Path("./standardized_dataset/")
DATASET_XLSXL_FILE = DATASET_EXPORT_DIR / "star_upper_gi_interface_export_test.xlsx"
EXAMINATION_NAME = "star_upper_gi_endoscopy"
# star_upper_gi_location_esophagogastric_junction

######### FINDINGS NORMAL
FINDINGS_NORMAL = [
    (
        "star_upper_gi_mucosa_esophagus_abnormal",
        [("yes_no_unknown_classification", "no")],
    ),
    (
        "star_upper_gi_imaging_modality_esophagus",
        [
            (
                "upper_gi_esophagus_imaging_modality_classification",
                "star_upper_gi_imaging_modality_white_light",
            ),
            (
                "upper_gi_esophagus_imaging_modality_classification",
                "star_upper_gi_imaging_modality_acidic_staining",
            ),
        ],
    ),
    (
        "star_upper_gi_mucosa_stomach_abnormal",
        [("yes_no_unknown_classification", "no")],
    ),
    (
        "star_upper_gi_chromoendoscopy_stomach",
        [("yes_no_unknown_classification", "no")],
    ),
    (
        "star_upper_gi_mucosa_stomach_abnormal",
        [("yes_no_unknown_classification", "no")],
    ),
    (
        "star_upper_gi_chromoendoscopy_stomach",
        [("yes_no_unknown_classification", "no")],
    ),
    (
        "star_upper_gi_mucosa_duodenum_abnormal",
        [("yes_no_unknown_classification", "no")],
    ),
    (
        "star_upper_gi_vili_duodenum_atrophic",
        [("yes_no_unknown_classification", "no")],
    ),
    (
        "star_upper_gi_papilla_major_visualized",
        [("yes_no_unknown_classification", "yes")],
    ),
    (
        "star_upper_gi_papilla_minor_visualized",
        [("yes_no_unknown_classification", "yes")],
    ),
]

FINDINGS_NORMAL_W_DESCRIPTORS = [
    (
        "star_upper_gi_location_esophagogastric_junction",
        [("distance_cm", "distance_cm", "length_cm_descriptor", "21.0")],
    ),
    (
        "star_upper_gi_location_hiatus",
        [("distance_cm", "distance_cm", "length_cm_descriptor", "21.0")],
    ),
    (
        "star_upper_gi_location_squamocolumnar_junction",
        [("distance_cm", "distance_cm", "length_cm_descriptor", "20.0")],
    ),
]

######### FINDINGS ABNORMAL
FINDINGS_ABNORMAL = [
    (
        "star_upper_gi_mucosa_esophagus_abnormal",
        [("yes_no_unknown_classification", "yes")],
    ),
    (
        "star_upper_gi_imaging_modality_esophagus",
        [
            (
                "upper_gi_esophagus_imaging_modality_classification",
                "star_upper_gi_imaging_modality_white_light",
            ),
            (
                "upper_gi_esophagus_imaging_modality_classification",
                "star_upper_gi_imaging_modality_acidic_staining",
            ),
        ],
    ),
    (
        "star_upper_gi_mucosa_stomach_abnormal",
        [("yes_no_unknown_classification", "yes")],
    ),
    (
        "star_upper_gi_chromoendoscopy_stomach",
        [("yes_no_unknown_classification", "yes")],
    ),
    (
        "star_upper_gi_mucosa_stomach_abnormal",
        [("yes_no_unknown_classification", "yes")],
    ),
    (
        "star_upper_gi_chromoendoscopy_stomach",
        [("yes_no_unknown_classification", "yes")],
    ),
    (
        "star_upper_gi_mucosa_duodenum_abnormal",
        [("yes_no_unknown_classification", "yes")],
    ),
    (
        "star_upper_gi_vili_duodenum_atrophic",
        [("yes_no_unknown_classification", "yes")],
    ),
    (
        "star_upper_gi_papilla_major_visualized",
        [("yes_no_unknown_classification", "yes")],
    ),
    (
        "star_upper_gi_papilla_minor_visualized",
        [("yes_no_unknown_classification", "yes")],
    ),
]

FINDINGS_ABNORMAL_W_DESCRIPTORS = [
    # Polyp Esophagus
    (
        "star_upper_gi_polyp",
        [
            (
                "star_upper_gi_location_classification",
                "star_upper_gi_location_esophagus_distal",
                None,
                None,
            ),
            (
                "star_upper_gi_location_esophagus_distance_z_line",
                "distance_cm",
                "length_cm_descriptor",
                "-2.0",
            ),
            (
                "size_oval_mm",
                "size_mm",
                "length_mm_descriptor",
                "8",
            ),
            (
                "star_upper_gi_lesion_paris",
                "star_upper_gi_paris_IIb",
                None,
                None,
            ),
            (
                "star_upper_gi_lesion_paris",
                "star_upper_gi_paris_IIc",
                None,
                None,
            ),
            (
                "additional_text_info",
                "additional_text_info",
                "additional_text_info",
                "Other Information not yet reflected in structured manner can be added here.",
            ),
        ],
    ),
    (
        "star_upper_gi_ulcer",
        [
            ("star_upper_gi_forrest", "star_upper_gi_forrest_III", None, None),
            (
                "star_upper_gi_location_classification",
                "star_upper_gi_location_duodenum_bulbus",
                None,
                None,
            ),
        ],
    ),
    (
        "star_upper_gi_ulcer",
        [
            ("star_upper_gi_forrest", "star_upper_gi_forrest_IIa", None, None),
            (
                "star_upper_gi_location_classification",
                "star_upper_gi_location_stomach_pylorus",
                None,
                None,
            ),
        ],
    ),
    (
        "star_upper_gi_esophagus_ectopic_mucosa",
        [
            ("distance_cm", "distance_cm", "length_cm_descriptor", "12.0"),
            ("size_oval_mm", "size_mm", "length_mm_descriptor", "5"),
        ],
    ),
]


class TestStarUpperGIData:
    def test_star_upper_gi_data_loading(
        self, star_ugi_knowledge_base: KnowledgeBase
    ) -> None:
        kb = star_ugi_knowledge_base
        assert kb.config.name == "star_upper_gi"

        kb.to_yaml(Path("./star_upper_gi_kb_export_test.yaml"))
        ledger = Ledger()
        db_interface = DbInterface(
            knowledge_base=kb,
            ledger=ledger,
        )
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

        for finding_name, classification_choice_tuples in FINDINGS_NORMAL_W_DESCRIPTORS:
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
                descriptor = (
                    db_interface.knowledge_base.get_classification_choice_descriptor(
                        name=descriptor_name
                    )
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
            for (
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
                descriptor = (
                    db_interface.knowledge_base.get_classification_choice_descriptor(
                        name=descriptor_name
                    )
                )
                p_classification_choice.create_descriptor(
                    descriptor=descriptor,
                    descriptor_value=descriptor_value,
                )

        dataset = interface2dataset(db_interface)
        dataset.to_csvs(DATASET_EXPORT_DIR)

        dataset.to_xlsx(DATASET_XLSXL_FILE, overwrite=True)

        db_interface.to_yaml(Path("./star_upper_gi_interface_export_test.yaml"))


# create patient examinations
## Normal

## Pathologic esophagus-varices

## pathologic stomach-ulcers

## pathologic duodenal diverticulum

## pathologic ectopic gastric mucosa

## export to yaml and csv

## validate knowledge base method

## validate interface method
