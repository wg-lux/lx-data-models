from typing import Final, NotRequired, TypedDict, cast

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
from lx_dtypes.models.ledger.p_electrical_application import (
    PElectricalApplication,
    PElectricalApplicationDataDict,
    PElectricalCurveComparison,
    PElectricalCurveComparisonDataDict,
)
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
from lx_dtypes.models.ledger.p_indication.DataDict import SerializedPIndicationDataDict
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
from lx_dtypes.models.ledger.p_time_offset import PTimeOffset, PTimeOffsetDataDict
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
    p_time_offsets: NotRequired[list[PTimeOffsetDataDict]]
    p_electrical_applications: NotRequired[list[PElectricalApplicationDataDict]]
    p_electrical_curve_comparisons: NotRequired[
        list[PElectricalCurveComparisonDataDict]
    ]
    reports: NotRequired[list[ReportDataDict]]
    patients: list[PatientDataDict]
    p_examinations: list[SerializedPExaminationDataDict]
    centers: list[CenterDataDict]
    examiners: list[ExaminerDataDict]
    p_findings: list[SerializedPFindingDataDict]
    p_indications: list[SerializedPIndicationDataDict]
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
    time_offsets: NotRequired[dict[str, PTimeOffsetDataDict]]
    electrical_applications: NotRequired[dict[str, PElectricalApplicationDataDict]]
    electrical_curve_comparisons: NotRequired[
        dict[str, PElectricalCurveComparisonDataDict]
    ]
    cases: dict[str, CaseDataDict]
    reports: NotRequired[dict[str, ReportDataDict]]
    video_files: NotRequired[dict[str, VideoFileDataDict]]
    patient_examinations: dict[str, PExaminationDataDict]
    patients: dict[str, PatientDataDict]
    centers: dict[str, CenterDataDict]
    examiners: dict[str, ExaminerDataDict]
    patient_videos: dict[str, PatientVideoFileDataDict]
    # raw_patient_videos: Dict[str, RawPatientVideoFileDataDict]


# Export key -> Ledger field for collections exported one record per entry.
FLAT_LEDGER_COLLECTIONS: Final[dict[str, str]] = {
    "p_time_offsets": "time_offsets",
    "p_electrical_applications": "electrical_applications",
    "p_electrical_curve_comparisons": "electrical_curve_comparisons",
    "reports": "reports",
    "patients": "patients",
    "centers": "centers",
    "examiners": "examiners",
    "video_files": "video_files",
    "p_videos": "patient_videos",
}
# Export keys of ``export_patient_examination_record_list``, in tuple order.
EXAMINATION_RECORD_LIST_KEYS: Final = (
    "p_examinations",
    "p_findings",
    "p_indications",
    "p_indication_classifications",
    "p_indication_classification_descriptors",
    "p_finding_classifications",
    "p_finding_classification_choices",
    "p_finding_classification_choice_descriptors",
    "p_finding_interventions",
    "p_finding_intervention",
)


class Ledger(AppBaseModelUUIDTags):
    time_offsets: dict[str, PTimeOffset] = Field(default_factory=dict)
    electrical_applications: dict[str, PElectricalApplication] = Field(
        default_factory=dict
    )
    electrical_curve_comparisons: dict[str, PElectricalCurveComparison] = Field(
        default_factory=dict
    )
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
        list[SerializedPIndicationDataDict],
        list[SerializedPIndicationClassificationDataDict],
        list[PIndicationClassificationDescriptorDataDict],
        list[SerializedPFindingClassificationsDataDict],
        list[SerializedPFindingClassificationChoiceDataDict],
        list[PFindingClassificationChoiceDescriptorDataDict],
        list[SerializedPFindingInterventionsDataDict],
        list[PFindingInterventionDataDict],
    ]:
        """Flatten every examination tree into one list per record level.

        Each level is traversed in parent order, so every list preserves the
        nesting order. Tuple order is the declared return order.
        """
        examinations = list(self.patient_examinations.values())
        indications = [i for e in examinations for i in e.patient_indications]
        indication_classifications = [
            c for i in indications for c in i.patient_indication_classifications
        ]
        indication_descriptors = [
            d
            for c in indication_classifications
            for d in c.patient_indication_classification_descriptors
        ]
        findings = [f for e in examinations for f in e.patient_findings]
        classifications = [
            c for f in findings for c in f.patient_finding_classifications
        ]
        choices = [
            c for g in classifications for c in g.patient_finding_classification_choices
        ]
        choice_descriptors = [
            d
            for c in choices
            for d in c.patient_finding_classification_choice_descriptors
        ]
        intervention_groups = [
            g for f in findings for g in f.patient_finding_interventions
        ]
        interventions = [
            i for g in intervention_groups for i in g.patient_finding_interventions
        ]
        return (
            [e.serialized_ddict for e in examinations],
            [f.serialized_ddict for f in findings],
            [i.serialized_ddict for i in indications],
            [c.serialized_ddict for c in indication_classifications],
            [d.ddict for d in indication_descriptors],
            [c.serialized_ddict for c in classifications],
            [c.serialized_ddict for c in choices],
            [d.ddict for d in choice_descriptors],
            [g.serialized_ddict for g in intervention_groups],
            [i.serialized_ddict for i in interventions],
        )

    def export_record_lists(self) -> LedgerRecordList:
        """Serialized records of every ledger collection, keyed as ``LedgerRecordList``.

        Flat collections come from ``FLAT_LEDGER_COLLECTIONS``; examination trees
        are flattened by ``export_patient_examination_record_list``.
        """
        records: dict[str, object] = {
            key: [record.serialized_ddict for record in getattr(self, field).values()]
            for key, field in FLAT_LEDGER_COLLECTIONS.items()
        }
        records.update(
            zip(
                EXAMINATION_RECORD_LIST_KEYS,
                self.export_patient_examination_record_list(),
                strict=True,
            )
        )
        return cast(LedgerRecordList, records)
