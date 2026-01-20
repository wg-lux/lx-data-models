from typing import Dict, List, Tuple, TypedDict

from pydantic import Field

# from lx_dtypes.factories.typed_dicts
from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.ledger.center import Center, CenterDataDict
from lx_dtypes.models.ledger.examiner.DataDict import ExaminerDataDict
from lx_dtypes.models.ledger.examiner.Pydantic import Examiner
from lx_dtypes.models.ledger.p_examination import PExamination, PExaminationDataDict
from lx_dtypes.models.ledger.p_finding.DataDict import PFindingDataDict
from lx_dtypes.models.ledger.p_finding_classification_choice.DataDict import (
    PFindingClassificationChoiceDataDict,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.DataDict import (
    PFindingClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.ledger.p_finding_classifications.DataDict import (
    PFindingClassificationsDataDict,
)
from lx_dtypes.models.ledger.p_indication.DataDict import PIndicationDataDict
from lx_dtypes.models.ledger.p_intervention.DataDict import PFindingInterventionDataDict
from lx_dtypes.models.ledger.p_interventions.DataDict import (
    PFindingInterventionsDataDict,
)
from lx_dtypes.models.ledger.patient import Patient, PatientDataDict


class LedgerRecordList(TypedDict):
    patients: List[PatientDataDict]
    p_examinations: List[PExaminationDataDict]
    centers: List[CenterDataDict]
    examiners: List[ExaminerDataDict]
    p_findings: List[PFindingDataDict]
    p_indications: List[PIndicationDataDict]
    p_finding_classifications: List[PFindingClassificationsDataDict]
    p_finding_classification_choices: List[PFindingClassificationChoiceDataDict]
    p_finding_classification_choice_descriptors: List[
        PFindingClassificationChoiceDescriptorDataDict
    ]
    p_finding_interventions: List[PFindingInterventionsDataDict]
    p_finding_intervention: List[PFindingInterventionDataDict]


class LedgerDataDict(AppBaseModelUUIDTagsDataDict):
    patient_examinations: Dict[str, PExaminationDataDict]
    patients: Dict[str, PatientDataDict]
    centers: Dict[str, CenterDataDict]


class Ledger(AppBaseModelUUIDTags):
    patient_examinations: Dict[str, PExamination] = Field(default_factory=dict)
    patients: Dict[str, Patient] = Field(default_factory=dict)
    centers: Dict[str, Center] = Field(default_factory=dict)
    examiners: Dict[str, Examiner] = Field(default_factory=dict)

    def patient_exists(self, patient_uuid: str) -> bool:
        return patient_uuid in self.patients

    def p_examination_exists(self, examination_uuid: str) -> bool:
        return examination_uuid in self.patient_examinations

    def export_patient_examination_record_list(self) -> Tuple[
        List[PExaminationDataDict],
        List[PFindingDataDict],
        List[PIndicationDataDict],
        List[PFindingClassificationsDataDict],
        List[PFindingClassificationChoiceDataDict],
        List[PFindingClassificationChoiceDescriptorDataDict],
        List[PFindingInterventionsDataDict],
        List[PFindingInterventionDataDict],
    ]:
        p_examination_dicts: List[PExaminationDataDict] = []
        p_finding_dicts: List[PFindingDataDict] = []
        p_indication_dicts: List[PIndicationDataDict] = []
        p_finding_classifications_dicts: List[PFindingClassificationsDataDict] = []
        p_finding_classification_choice_dicts: List[
            PFindingClassificationChoiceDataDict
        ] = []
        p_finding_classification_choice_descriptor_dicts: List[
            PFindingClassificationChoiceDescriptorDataDict
        ] = []
        p_finding_interventions_dicts: List[PFindingInterventionsDataDict] = []
        p_finding_intervention_dicts: List[PFindingInterventionDataDict] = []

        for p_examination in self.patient_examinations.values():
            # 1. Export PExamination
            p_examination_dicts.append(p_examination.ddict)

            # 2. Export PIndication
            for p_indication in p_examination.patient_indications:
                p_indication_dicts.append(p_indication.ddict)

            # 3. Export PFinding and nested classifications
            for p_finding in p_examination.patient_findings:
                p_finding_dicts.append(p_finding.ddict)

                # 4. Export PFindingClassifications and nested choices
                for (
                    p_finding_classifications
                ) in p_finding.patient_finding_classifications:
                    p_finding_classifications_dicts.append(
                        p_finding_classifications.ddict
                    )

                    # 5. Export PFindingClassificationChoice and nested descriptors
                    for (
                        p_finding_classification_choice
                    ) in (
                        p_finding_classifications.patient_finding_classification_choices
                    ):
                        p_finding_classification_choice_dicts.append(
                            p_finding_classification_choice.ddict
                        )

                        # 6. Export PFindingClassificationChoiceDescriptor
                        for (
                            p_finding_classification_choice_descriptor
                        ) in (
                            p_finding_classification_choice.patient_finding_classification_choice_descriptors
                        ):
                            p_finding_classification_choice_descriptor_dicts.append(
                                p_finding_classification_choice_descriptor.ddict
                            )
                # 7. Export PFindingInterventions and nested PFindingIntervention
                for p_finding_interventions in p_finding.patient_finding_interventions:
                    p_finding_interventions_dicts.append(p_finding_interventions.ddict)

                    # 8. Export PFindingIntervention
                    for (
                        p_finding_intervention
                    ) in p_finding_interventions.patient_finding_interventions:
                        p_finding_intervention_dicts.append(
                            p_finding_intervention.ddict
                        )

        return (
            p_examination_dicts,
            p_finding_dicts,
            p_indication_dicts,
            p_finding_classifications_dicts,
            p_finding_classification_choice_dicts,
            p_finding_classification_choice_descriptor_dicts,
            p_finding_interventions_dicts,
            p_finding_intervention_dicts,
        )

    def export_record_lists(self) -> LedgerRecordList:
        patient_dicts: List[PatientDataDict] = [r.ddict for r in self.patients.values()]
        examiner_dicts: List[ExaminerDataDict] = [
            r.ddict for r in self.examiners.values()
        ]
        center_dicts: List[CenterDataDict] = [r.ddict for r in self.centers.values()]

        (
            p_examination_dicts,
            p_finding_dicts,
            p_indication_dicts,
            p_finding_classifications_dicts,
            p_finding_classification_choice_dicts,
            p_finding_classification_choice_descriptor_dicts,
            p_finding_interventions_dicts,
            p_finding_intervention_dicts,
        ) = self.export_patient_examination_record_list()

        record_list: LedgerRecordList = LedgerRecordList(
            patients=patient_dicts,
            p_examinations=p_examination_dicts,
            centers=center_dicts,
            examiners=examiner_dicts,
            p_findings=p_finding_dicts,
            p_indications=p_indication_dicts,
            p_finding_classifications=p_finding_classifications_dicts,
            p_finding_classification_choices=p_finding_classification_choice_dicts,
            p_finding_classification_choice_descriptors=p_finding_classification_choice_descriptor_dicts,
            p_finding_interventions=p_finding_interventions_dicts,
            p_finding_intervention=p_finding_intervention_dicts,
        )
        return record_list
