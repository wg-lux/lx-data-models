from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lx_dtypes.models.interface.DbInterface import DbInterface
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.Ledger import Ledger
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

EXAMINATION_NAME = "star_upper_gi_endoscopy"

type ClassificationChoiceTuple = tuple[str, str]
type DescriptorClassificationChoiceTuple = tuple[str, str, str | None, str | None]
type FindingWithChoices = tuple[str, list[ClassificationChoiceTuple]]
type FindingWithDescriptorChoices = tuple[
    str, list[DescriptorClassificationChoiceTuple]
]

FINDINGS_NORMAL: list[FindingWithChoices] = [
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

FINDINGS_NORMAL_W_DESCRIPTORS: list[FindingWithDescriptorChoices] = [
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

FINDINGS_ABNORMAL: list[FindingWithChoices] = [
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

FINDINGS_ABNORMAL_W_DESCRIPTORS: list[FindingWithDescriptorChoices] = [
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
            ("size_oval_mm", "size_mm", "length_mm_descriptor", "8"),
            ("star_upper_gi_lesion_paris", "star_upper_gi_paris_IIb", None, None),
            ("star_upper_gi_lesion_paris", "star_upper_gi_paris_IIc", None, None),
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
    (
        "star_upper_gi_esophagus_barretts",
        [
            (
                "star_upper_gi_barrett_praque_classification",
                "star_upper_gi_barrett_praque_c_value",
                "length_cm_descriptor",
                "3.0",
            ),
            (
                "star_upper_gi_barrett_praque_classification",
                "star_upper_gi_barrett_praque_m_value",
                "length_cm_descriptor",
                "4.0",
            ),
        ],
    ),
    (
        "star_upper_gi_esophagus_varices",
        [
            (
                "star_upper_gi_esophagus_varices_baveno",
                "star_upper_gi_esophagus_varices_baveno_small",
                None,
                None,
            ),
            (
                "additional_text_info",
                "additional_text_info",
                "additional_text_info",
                "1 varices noted, no red wale markings.",
            ),
        ],
    ),
    (
        "star_upper_gi_esophagus_diverticulum",
        [
            ("distance_cm", "distance_cm", "length_cm_descriptor", "8.0"),
            ("size_oval_mm", "size_mm", "length_mm_descriptor", "6"),
        ],
    ),
    (
        "star_upper_gi_esophagitis",
        [
            (
                "star_upper_gi_los_angeles_classification",
                "star_upper_gi_los_angeles_classification_a",
                None,
                None,
            ),
        ],
    ),
    (
        "star_upper_gi_esophagitis_eosinophilic",
        [
            (
                "star_upper_gi_erefs_edema",
                "star_upper_gi_erefs_edema_present",
                None,
                None,
            ),
            (
                "star_upper_gi_erefs_rings",
                "star_upper_gi_erefs_rings_moderate",
                None,
                None,
            ),
            (
                "star_upper_gi_erefs_exudates",
                "star_upper_gi_erefs_exudates_mild",
                None,
                None,
            ),
            (
                "star_upper_gi_erefs_furrows",
                "star_upper_gi_erefs_furrows_present",
                None,
                None,
            ),
            (
                "star_upper_gi_erefs_strictures",
                "star_upper_gi_erefs_strictures_none",
                None,
                None,
            ),
        ],
    ),
    (
        "star_upper_gi_esophagitis_caustic",
        [
            ("star_upper_gi_zargar", "star_upper_gi_zargar_grade_2a", None, None),
        ],
    ),
    (
        "star_upper_gi_stomach_varices",
        [
            (
                "star_upper_gi_stomach_varices_sarin",
                "star_upper_gi_stomach_varices_sarin_gov1",
                None,
                None,
            ),
        ],
    ),
    (
        "star_upper_gi_stomach_varices",
        [
            (
                "star_upper_gi_stomach_varices_sarin",
                "star_upper_gi_stomach_varices_sarin_igv2",
                None,
                None,
            ),
        ],
    ),
    (
        "star_upper_gi_duodenum_diverticulum",
        [
            (
                "star_upper_gi_location_duodenum",
                "star_upper_gi_location_duodenum_descending_part",
                None,
                None,
            ),
            ("size_oval_mm", "size_mm", "length_mm_descriptor", "4"),
        ],
    ),
]


@dataclass(frozen=True)
class DemoStarUpperGiExportPaths:
    base_dir: Path
    knowledge_base_yaml: Path
    interface_yaml: Path
    dataset_dir: Path
    dataset_xlsx: Path


def build_demo_star_upper_gi_export_paths(base_dir: Path) -> DemoStarUpperGiExportPaths:
    demo_dir = base_dir / "demo"
    dataset_dir = demo_dir / "standardized_dataset"
    return DemoStarUpperGiExportPaths(
        base_dir=demo_dir,
        knowledge_base_yaml=demo_dir / "demo_kb_export.yaml",
        interface_yaml=demo_dir / "demo_interface_export.yaml",
        dataset_dir=dataset_dir,
        dataset_xlsx=dataset_dir / "demo_interface_export.xlsx",
    )


def _apply_findings(
    db_interface: DbInterface,
    *,
    patient_examination: PExamination,
    findings: list[FindingWithChoices],
) -> None:
    for finding_name, classification_choice_tuples in findings:
        patient_finding = db_interface.create_examination_finding(
            patient_examination=patient_examination,
            finding=finding_name,
        )
        for (
            classification_name,
            classification_choice_name,
        ) in classification_choice_tuples:
            db_interface.create_patient_finding_classification_choice(
                patient_examination=patient_examination,
                patient_finding=patient_finding,
                classification=classification_name,
                classification_choice=classification_choice_name,
            )


def _apply_descriptor_findings(
    db_interface: DbInterface,
    *,
    patient_examination: PExamination,
    findings: list[FindingWithDescriptorChoices],
) -> None:
    for finding_name, classification_choice_tuples in findings:
        patient_finding = db_interface.create_examination_finding(
            patient_examination=patient_examination,
            finding=finding_name,
        )
        for (
            classification_name,
            classification_choice_name,
            descriptor_name,
            descriptor_value,
        ) in classification_choice_tuples:
            patient_classification_choice = (
                db_interface.create_patient_finding_classification_choice(
                    patient_examination=patient_examination,
                    patient_finding=patient_finding,
                    classification=classification_name,
                    classification_choice=classification_choice_name,
                )
            )
            if not descriptor_name or descriptor_value is None:
                continue
            descriptor = (
                db_interface.knowledge_base.get_classification_choice_descriptor(
                    name=descriptor_name
                )
            )
            patient_classification_choice.create_descriptor(
                descriptor=descriptor,
                descriptor_value=descriptor_value,
            )


def build_star_upper_gi_demo_interface(knowledge_base: KnowledgeBase) -> DbInterface:
    ledger = Ledger()
    db_interface = DbInterface(
        knowledge_base=knowledge_base,
        ledger=ledger,
    )
    patient = db_interface.create_patient(
        first_name="John",
        last_name="Doe",
        dob="1980-01-01",
    )

    normal_exam = db_interface.create_patient_examination(
        patient=patient,
        examination=EXAMINATION_NAME,
    )
    _apply_findings(
        db_interface,
        patient_examination=normal_exam,
        findings=FINDINGS_NORMAL,
    )
    _apply_descriptor_findings(
        db_interface,
        patient_examination=normal_exam,
        findings=FINDINGS_NORMAL_W_DESCRIPTORS,
    )

    abnormal_exam = db_interface.create_patient_examination(
        patient=patient,
        examination=EXAMINATION_NAME,
    )
    _apply_findings(
        db_interface,
        patient_examination=abnormal_exam,
        findings=FINDINGS_ABNORMAL,
    )
    _apply_descriptor_findings(
        db_interface,
        patient_examination=abnormal_exam,
        findings=FINDINGS_ABNORMAL_W_DESCRIPTORS,
    )

    return db_interface
