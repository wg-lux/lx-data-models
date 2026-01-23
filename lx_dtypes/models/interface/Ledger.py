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
from lx_dtypes.models.ledger.p_intervention.DataDict import PFindingInterventionDataDict
from lx_dtypes.models.ledger.p_interventions.DataDict import (
    SerializedPFindingInterventionsDataDict,
)
from lx_dtypes.models.ledger.patient import Patient, PatientDataDict


class LedgerRecordList(TypedDict):
    patients: List[PatientDataDict]
    p_examinations: List[SerializedPExaminationDataDict]
    centers: List[CenterDataDict]
    examiners: List[ExaminerDataDict]
    p_findings: List[SerializedPFindingDataDict]
    p_indications: List[PIndicationDataDict]
    p_finding_classifications: List[SerializedPFindingClassificationsDataDict]
    p_finding_classification_choices: List[
        SerializedPFindingClassificationChoiceDataDict
    ]
    p_finding_classification_choice_descriptors: List[
        PFindingClassificationChoiceDescriptorDataDict
    ]
    p_finding_interventions: List[SerializedPFindingInterventionsDataDict]
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
        """
        Check whether a patient with the given UUID exists in the ledger.

        Returns:
            `true` if a patient with the given UUID exists, `false` otherwise.
        """
        return patient_uuid in self.patients

    def p_examination_exists(self, examination_uuid: str) -> bool:
        """
        Check whether a patient examination with the given UUID exists in the ledger.

        Returns:
            `True` if an examination with the given UUID is present in `self.patient_examinations`, `False` otherwise.
        """
        return examination_uuid in self.patient_examinations

    def export_patient_examination_record_list(
        self,
    ) -> Tuple[
        List[SerializedPExaminationDataDict],
        List[SerializedPFindingDataDict],
        List[PIndicationDataDict],
        List[SerializedPFindingClassificationsDataDict],
        List[SerializedPFindingClassificationChoiceDataDict],
        List[PFindingClassificationChoiceDescriptorDataDict],
        List[SerializedPFindingInterventionsDataDict],
        List[PFindingInterventionDataDict],
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
        p_examination_dicts: List[SerializedPExaminationDataDict] = []
        p_finding_dicts: List[SerializedPFindingDataDict] = []
        p_indication_dicts: List[PIndicationDataDict] = []
        p_finding_classifications_dicts: List[
            SerializedPFindingClassificationsDataDict
        ] = []
        p_finding_classification_choice_dicts: List[
            SerializedPFindingClassificationChoiceDataDict
        ] = []
        p_finding_classification_choice_descriptor_dicts: List[
            PFindingClassificationChoiceDescriptorDataDict
        ] = []
        p_finding_interventions_dicts: List[
            SerializedPFindingInterventionsDataDict
        ] = []
        p_finding_intervention_dicts: List[PFindingInterventionDataDict] = []

        for p_examination in self.patient_examinations.values():
            # 1. Export PExamination
            p_examination_dicts.append(p_examination.serialized_ddict)

            # 2. Export PIndication
            for p_indication in p_examination.patient_indications:
                p_indication_dicts.append(p_indication.serialized_ddict)

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
        """
        patient_dicts: List[PatientDataDict] = [
            r.serialized_ddict for r in self.patients.values()
        ]
        examiner_dicts: List[ExaminerDataDict] = [
            r.serialized_ddict for r in self.examiners.values()
        ]
        center_dicts: List[CenterDataDict] = [
            r.serialized_ddict for r in self.centers.values()
        ]

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
