from typing import NotRequired, TypedDict

from pydantic import Field

# from lx_dtypes.factories.typed_dicts
from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.ledger.case import Case, CaseDataDict
from lx_dtypes.models.ledger.center import Center, CenterDataDict
from lx_dtypes.models.ledger.examiner.DataDict import ExaminerDataDict
from lx_dtypes.models.ledger.examiner.Pydantic import Examiner
from lx_dtypes.models.ledger.p_examination import PExamination, PExaminationDataDict
from lx_dtypes.models.ledger.p_examination.DataDict import (
    SerializedPExaminationDataDict,
)
from lx_dtypes.models.ledger.p_finding.DataDict import (
    SerializedPFindingDataDict,
)
from lx_dtypes.models.ledger.p_finding_classification_choice.DataDict import (
    SerializedPFindingClassificationChoiceDataDict,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.DataDict import (
    PFindingClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.ledger.p_finding_classifications.DataDict import (
    SerializedPFindingClassificationsDataDict,
)
from lx_dtypes.models.ledger.p_indication.DataDict import PIndicationDataDict
from lx_dtypes.models.ledger.p_indication_classification.DataDict import (
    SerializedPIndicationClassificationDataDict,
)
from lx_dtypes.models.ledger.p_indication_classification_descriptor.DataDict import (
    PIndicationClassificationDescriptorDataDict,
)
from lx_dtypes.models.ledger.p_intervention.DataDict import PFindingInterventionDataDict
from lx_dtypes.models.ledger.p_interventions.DataDict import (
    SerializedPFindingInterventionsDataDict,
)
from lx_dtypes.models.ledger.p_video import (
    PatientVideoFile,
    PatientVideoFileDataDict,
    # RawPatientVideoFileDataDict,
    # RawVideoFile,
)
from lx_dtypes.models.ledger.patient import Patient, PatientDataDict
from lx_dtypes.models.ledger.report import Report, ReportDataDict
from lx_dtypes.models.ledger.video_file import VideoFile, VideoFileDataDict


class LedgerRecordList(TypedDict):
    reports: NotRequired[list[ReportDataDict]]
    patients: list[PatientDataDict]
    p_examinations: list[SerializedPExaminationDataDict]
    centers: list[CenterDataDict]
    examiners: list[ExaminerDataDict]
    p_findings: list[SerializedPFindingDataDict]
    p_indications: list[PIndicationDataDict]
    p_indication_classifications: list[SerializedPIndicationClassificationDataDict]
    p_indication_classification_descriptors: list[
        PIndicationClassificationDescriptorDataDict
    ]
    p_finding_classifications: list[SerializedPFindingClassificationsDataDict]
    p_finding_classification_choices: list[
        SerializedPFindingClassificationChoiceDataDict
    ]
    p_finding_classification_choice_descriptors: list[
        PFindingClassificationChoiceDescriptorDataDict
    ]
    p_finding_interventions: list[SerializedPFindingInterventionsDataDict]
    p_finding_intervention: list[PFindingInterventionDataDict]
    video_files: NotRequired[list[VideoFileDataDict]]
    p_videos: list[PatientVideoFileDataDict]
    # p_raw_videos: List[RawPatientVideoFileDataDict]


class LedgerDataDict(AppBaseModelUUIDTagsDataDict):
    cases: dict[str, CaseDataDict]
    reports: NotRequired[dict[str, ReportDataDict]]
    video_files: NotRequired[dict[str, VideoFileDataDict]]
    patient_examinations: dict[str, PExaminationDataDict]
    patients: dict[str, PatientDataDict]
    centers: dict[str, CenterDataDict]
    patient_videos: dict[str, PatientVideoFileDataDict]
    # raw_patient_videos: Dict[str, RawPatientVideoFileDataDict]


class Ledger(AppBaseModelUUIDTags):
    cases: dict[str, Case] = Field(default_factory=dict)
    reports: dict[str, Report] = Field(default_factory=dict)
    patient_examinations: dict[str, PExamination] = Field(default_factory=dict)
    patients: dict[str, Patient] = Field(default_factory=dict)
    centers: dict[str, Center] = Field(default_factory=dict)
    examiners: dict[str, Examiner] = Field(default_factory=dict)
    video_files: dict[str, VideoFile] = Field(default_factory=dict)
    patient_videos: dict[str, PatientVideoFile] = Field(default_factory=dict)
    # raw_patient_videos: Dict[str, RawVideoFile] = Field(default_factory=dict)
    # patient_images: Dict[str, PFile] = Field(default_factory=dict)
    # patient_pdfs: Dict[str, PFile] = Field(default_factory=dict)
    # video_segment_annotations
    # image_annotations

    def patient_exists(self, patient_uuid: str) -> bool:
        """
        Check whether a patient with the given UUID exists in the ledger.

        Returns:
            `true` if a patient with the given UUID exists, `false` otherwise.
        """
        return patient_uuid in self.patients

    def case_exists(self, case_uuid: str) -> bool:
        """Return whether a transient case with this UUID is present."""
        return case_uuid in self.cases

    def p_examination_exists(self, examination_uuid: str) -> bool:
        """
        Check whether a patient examination with the given UUID exists in the ledger.

        Returns:
            `True` if an examination with the given UUID is present in `self.patient_examinations`, `False` otherwise.
        """
        return examination_uuid in self.patient_examinations

    def export_patient_examination_record_list(
        self,
    ) -> tuple[
        list[SerializedPExaminationDataDict],
        list[SerializedPFindingDataDict],
        list[PIndicationDataDict],
        list[SerializedPIndicationClassificationDataDict],
        list[PIndicationClassificationDescriptorDataDict],
        list[SerializedPFindingClassificationsDataDict],
        list[SerializedPFindingClassificationChoiceDataDict],
        list[PFindingClassificationChoiceDescriptorDataDict],
        list[SerializedPFindingInterventionsDataDict],
        list[PFindingInterventionDataDict],
    ]:
        """
        Collects and serializes all patient-examination-related records into eight separate lists.

        Returns:
            Tuple containing, in order:
            - p_examination_dicts (List[SerializedPExaminationDataDict]): Serialized patient examination records.
            - p_finding_dicts (List[SerializedPFindingDataDict]): Serialized findings associated with examinations.
            - p_indication_dicts (List[PIndicationDataDict]): Serialized indications associated with examinations.
            - p_finding_classifications_dicts (List[SerializedPFindingClassificationsDataDict]): Serialized finding-classification records.
            - p_finding_classification_choice_dicts (List[SerializedPFindingClassificationChoiceDataDict]): Serialized classification choice records.
            - p_finding_classification_choice_descriptor_dicts (List[PFindingClassificationChoiceDescriptorDataDict]): Descriptor dictionaries for classification choices.
            - p_finding_interventions_dicts (List[SerializedPFindingInterventionsDataDict]): Serialized intervention-group records for findings.
            - p_finding_intervention_dicts (List[PFindingInterventionDataDict]): Serialized individual intervention records.
        """
        p_examination_dicts: list[SerializedPExaminationDataDict] = []
        p_finding_dicts: list[SerializedPFindingDataDict] = []
        p_indication_dicts: list[PIndicationDataDict] = []
        p_indication_classification_dicts: list[
            SerializedPIndicationClassificationDataDict
        ] = []
        p_indication_classification_descriptor_dicts: list[
            PIndicationClassificationDescriptorDataDict
        ] = []
        p_finding_classifications_dicts: list[
            SerializedPFindingClassificationsDataDict
        ] = []
        p_finding_classification_choice_dicts: list[
            SerializedPFindingClassificationChoiceDataDict
        ] = []
        p_finding_classification_choice_descriptor_dicts: list[
            PFindingClassificationChoiceDescriptorDataDict
        ] = []
        p_finding_interventions_dicts: list[
            SerializedPFindingInterventionsDataDict
        ] = []
        p_finding_intervention_dicts: list[PFindingInterventionDataDict] = []

        for p_examination in self.patient_examinations.values():
            # 1. Export PExamination
            p_examination_dicts.append(p_examination.serialized_ddict)

            # 2. Export PIndication
            for p_indication in p_examination.patient_indications:
                p_indication_dicts.append(p_indication.serialized_ddict)
                for (
                    p_indication_classification
                ) in p_indication.patient_indication_classifications:
                    p_indication_classification_dicts.append(
                        p_indication_classification.serialized_ddict
                    )
                    for p_indication_classification_descriptor in p_indication_classification.patient_indication_classification_descriptors:
                        p_indication_classification_descriptor_dicts.append(
                            p_indication_classification_descriptor.ddict
                        )

            # 3. Export PFinding and nested classifications
            for p_finding in p_examination.patient_findings:
                p_finding_dicts.append(p_finding.serialized_ddict)

                # 4. Export PFindingClassifications and nested choices
                for (
                    p_finding_classifications
                ) in p_finding.patient_finding_classifications:
                    p_finding_classifications_dicts.append(
                        p_finding_classifications.serialized_ddict
                    )

                    # 5. Export PFindingClassificationChoice and nested descriptors
                    for p_finding_classification_choice in (
                        p_finding_classifications.patient_finding_classification_choices
                    ):
                        p_finding_classification_choice_dicts.append(
                            p_finding_classification_choice.serialized_ddict
                        )

                        # 6. Export PFindingClassificationChoiceDescriptor
                        for p_finding_classification_choice_descriptor in p_finding_classification_choice.patient_finding_classification_choice_descriptors:
                            p_finding_classification_choice_descriptor_dicts.append(
                                p_finding_classification_choice_descriptor.ddict
                            )
                # 7. Export PFindingInterventions and nested PFindingIntervention
                for p_finding_interventions in p_finding.patient_finding_interventions:
                    p_finding_interventions_dicts.append(
                        p_finding_interventions.serialized_ddict
                    )

                    # 8. Export PFindingIntervention
                    for (
                        p_finding_intervention
                    ) in p_finding_interventions.patient_finding_interventions:
                        p_finding_intervention_dicts.append(
                            p_finding_intervention.serialized_ddict
                        )

        return (
            p_examination_dicts,
            p_finding_dicts,
            p_indication_dicts,
            p_indication_classification_dicts,
            p_indication_classification_descriptor_dicts,
            p_finding_classifications_dicts,
            p_finding_classification_choice_dicts,
            p_finding_classification_choice_descriptor_dicts,
            p_finding_interventions_dicts,
            p_finding_intervention_dicts,
        )

    def export_record_lists(self) -> LedgerRecordList:
        """
        Collects serialized representations of all ledger entities and returns them as a LedgerRecordList suitable for export.

        The returned record list contains flattened lists for patients, patient examinations, centers, examiners, findings, indications, finding classifications, classification choices, classification choice descriptors, finding interventions, and individual finding intervention records.

        Returns:
            LedgerRecordList: A TypedDict with these keys populated:
                - patients: List of patient data dicts.
                - p_examinations: List of serialized patient examination data dicts.
                - centers: List of center data dicts.
                - examiners: List of examiner data dicts.
                - p_findings: List of serialized finding data dicts.
                - p_indications: List of indication data dicts.
                - p_finding_classifications: List of serialized finding classifications data dicts.
                - p_finding_classification_choices: List of serialized classification choice data dicts.
                - p_finding_classification_choice_descriptors: List of classification choice descriptor data dicts.
                - p_finding_interventions: List of serialized finding interventions data dicts.
                - p_finding_intervention: List of individual finding intervention data dicts.
                - video_files: List of serialized technical VideoFile records.
                - patient_video_file_dicts (List[PatientVideoFileDataDict]): Serialized patient video file records.
        """
        report_dicts: list[ReportDataDict] = [
            r.serialized_ddict for r in self.reports.values()
        ]
        patient_dicts: list[PatientDataDict] = [
            r.serialized_ddict for r in self.patients.values()
        ]
        examiner_dicts: list[ExaminerDataDict] = [
            r.serialized_ddict for r in self.examiners.values()
        ]
        center_dicts: list[CenterDataDict] = [
            r.serialized_ddict for r in self.centers.values()
        ]

        video_file_dicts: list[VideoFileDataDict] = [
            r.serialized_ddict for r in self.video_files.values()
        ]
        video_dicts = [r.serialized_ddict for r in self.patient_videos.values()]
        # raw_video_dicts = [r.serialized_ddict for r in self.raw_patient_videos.values()]

        (
            p_examination_dicts,
            p_finding_dicts,
            p_indication_dicts,
            p_indication_classification_dicts,
            p_indication_classification_descriptor_dicts,
            p_finding_classifications_dicts,
            p_finding_classification_choice_dicts,
            p_finding_classification_choice_descriptor_dicts,
            p_finding_interventions_dicts,
            p_finding_intervention_dicts,
        ) = self.export_patient_examination_record_list()

        record_list: LedgerRecordList = LedgerRecordList(
            reports=report_dicts,
            patients=patient_dicts,
            p_examinations=p_examination_dicts,
            centers=center_dicts,
            examiners=examiner_dicts,
            p_findings=p_finding_dicts,
            p_indications=p_indication_dicts,
            p_indication_classifications=p_indication_classification_dicts,
            p_indication_classification_descriptors=(
                p_indication_classification_descriptor_dicts
            ),
            p_finding_classifications=p_finding_classifications_dicts,
            p_finding_classification_choices=p_finding_classification_choice_dicts,
            p_finding_classification_choice_descriptors=p_finding_classification_choice_descriptor_dicts,
            p_finding_interventions=p_finding_interventions_dicts,
            p_finding_intervention=p_finding_intervention_dicts,
            video_files=video_file_dicts,
            p_videos=video_dicts,
            # p_raw_videos=raw_video_dicts,
        )
        return record_list
