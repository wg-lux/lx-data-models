from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Self

import yaml

from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase, KnowledgeBaseDDict
from lx_dtypes.models.interface.Ledger import Ledger, LedgerDataDict
from lx_dtypes.models.knowledge_base.classification.Classification import (
    Classification,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.examination import Examination
from lx_dtypes.models.knowledge_base.finding._Finding import Finding
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding
from lx_dtypes.models.ledger.p_finding_classification_choice.Pydantic import (
    PFindingClassificationChoice,
)
from lx_dtypes.models.ledger.p_finding_classifications.Pydantic import (
    PFindingClassifications,
)
from lx_dtypes.models.ledger.patient.Pydantic import Patient


class DbInterfaceDataDict(
    AppBaseModelUUIDTagsDataDict,
):
    knowledge_base: KnowledgeBaseDDict
    ledger: LedgerDataDict


class DbInterface(AppBaseModelUUIDTags):
    knowledge_base: KnowledgeBase
    ledger: Ledger

    @classmethod
    def create_from_yaml(cls, yaml_path: Path) -> Self:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data_dict = yaml.safe_load(f)

        kb = cls.model_validate(data_dict)
        return kb

    @classmethod
    def create_empty(cls, name: str, version: str) -> Self:
        from lx_dtypes.models.interface.KnowledgeBaseConfig import (
            KnowledgeBaseConfig,
        )

        kb_cfg = KnowledgeBaseConfig(name=name, version=version)
        db_interface = cls.model_validate(
            {
                "knowledge_base": KnowledgeBase.create_from_config(kb_cfg),
                "ledger": Ledger(),
            }
        )
        return db_interface

    def create_patient(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        dob: Optional[str | date] = None,
    ) -> Patient:
        kwargs = {}
        if first_name is not None:
            kwargs["first_name"] = first_name
        if last_name is not None:
            kwargs["last_name"] = last_name
        if dob is not None:
            if isinstance(dob, date):
                # tp str
                dob = dob.isoformat()
            kwargs["dob"] = dob

        patient = Patient(**kwargs)  # type: ignore # TODO mypy issue with dynamic kwargs
        self.ledger.patients[str(patient.uuid)] = patient
        return patient

    def create_patient_examination(
        self, patient: Patient | str, examination: Examination | str
    ) -> PExamination:
        if isinstance(patient, Patient):
            patient_uuid = str(patient.uuid)
        else:
            patient_uuid = patient

        if not self.ledger.patient_exists(patient_uuid):
            raise ValueError(
                f"Patient with UUID {patient_uuid} does not exist in the ledger."
            )

        if isinstance(examination, Examination):
            examination_name = examination.name
        else:
            examination_name = examination

        try:
            self.knowledge_base.get_examination(examination_name)
        except KeyError:
            raise ValueError(
                f"Examination '{examination_name}' does not exist in the knowledge base."
            )
        p_examination = PExamination(patient=patient_uuid, examination=examination_name)

        self.ledger.patient_examinations[str(p_examination.uuid)] = p_examination
        return p_examination

    def create_examination_finding(
        self, patient_examination: PExamination | str, finding: Finding | str
    ) -> PFinding:
        if isinstance(patient_examination, PExamination):
            p_examination_uuid = str(patient_examination.uuid)
        else:
            p_examination_uuid = patient_examination

        if not self.ledger.p_examination_exists(p_examination_uuid):
            raise ValueError(
                f"Patient Examination with UUID {p_examination_uuid} does not exist in the ledger."
            )
        p_examination = self.ledger.patient_examinations[p_examination_uuid]

        if isinstance(finding, Finding):
            finding_name = finding.name
        else:
            finding_name = finding

        try:
            _finding_obj = self.knowledge_base.get_finding(finding_name)
        except KeyError:
            raise ValueError(
                f"Finding '{finding_name}' does not exist in the knowledge base."
            )

        examination_obj = self.knowledge_base.get_examination(p_examination.examination)

        assert finding_name in examination_obj.findings, (
            f"Finding '{finding_name}' is not linked to Examination '{examination_obj.name}'."
        )

        p_examination = self.ledger.patient_examinations[p_examination_uuid]

        p_finding = PFinding(
            patient_examination=p_examination_uuid,
            finding=finding_name,
        )
        p_finding_classifications = PFindingClassifications(
            patient_finding=str(p_finding.uuid),
        )

        p_finding.patient_finding_classifications = [p_finding_classifications]

        p_examination.patient_findings.append(p_finding)

        self.ledger.patient_examinations[p_examination_uuid] = p_examination
        return p_finding

    def create_patient_finding_classification_choice(
        self,
        patient_examination: PExamination | str,
        patient_finding: PFinding | str,
        classification: Classification | str,
        classification_choice: ClassificationChoice | str,
        patient_finding_classifications: Optional[PFindingClassifications | str] = None,
    ) -> PFindingClassificationChoice:
        # Patient Examination existence check
        if isinstance(patient_examination, PExamination):
            p_examination_uuid = str(patient_examination.uuid)
        else:
            p_examination_uuid = patient_examination

        if not self.ledger.p_examination_exists(p_examination_uuid):
            raise ValueError(
                f"Patient Examination with UUID {p_examination_uuid} does not exist in the ledger."
            )

        # Patient Finding existence check
        if isinstance(patient_finding, PFinding):
            p_finding_uuid = str(patient_finding.uuid)
        else:
            p_finding_uuid = patient_finding

        p_examination = self.ledger.patient_examinations[p_examination_uuid]
        p_finding = p_examination.get_finding_by_uuid(p_finding_uuid)

        # Patient Finding Classifications existence check
        if isinstance(patient_finding_classifications, PFindingClassifications):
            p_finding_classifications_uuid = str(patient_finding_classifications.uuid)
            p_finding_classifications = p_finding.get_p_classifications_by_uuid(
                p_finding_classifications_uuid
            )
        elif isinstance(patient_finding_classifications, str):
            p_finding_classifications_uuid = patient_finding_classifications
            p_finding_classifications = p_finding.get_p_classifications_by_uuid(
                p_finding_classifications_uuid
            )

        else:
            assert patient_finding_classifications is None
            p_finding_classifications = p_finding.latest_classifications_obj
            p_finding_classifications_uuid = str(p_finding_classifications.uuid)

        # Classification existence check
        if isinstance(classification, Classification):
            classification_name = classification.name
        else:
            classification_name = classification
        # Make sure classification is linked to finding
        finding_obj = self.knowledge_base.get_finding(p_finding.finding)
        assert classification_name in finding_obj.classifications, (
            f"Classification '{classification_name}' is not linked to Finding '{finding_obj.name}'."
        )

        try:
            classification_obj = self.knowledge_base.get_classification(
                classification_name
            )
        except KeyError:
            raise ValueError(
                f"Classification '{classification_name}' does not exist in the knowledge base."
            )

        # Classification Choice existence check
        if isinstance(classification_choice, ClassificationChoice):
            classification_choice_name = classification_choice.name
        else:
            classification_choice_name = classification_choice

        try:
            _classification_choice_obj = self.knowledge_base.get_classification_choice(
                classification_choice_name
            )
        except KeyError:
            raise ValueError(
                f"Classification Choice '{classification_choice_name}' does not exist in the knowledge base."
            )

        # Make sure that the classification choice belongs to the classification
        assert (
            classification_choice_name in classification_obj.classification_choices
        ), (
            f"Classification Choice '{classification_choice_name}' does not belong to Classification '{classification_name}'."
        )

        # create PFindingClassificationChoice
        p_finding_classification_choice = PFindingClassificationChoice(
            patient_finding_classifications=p_finding_classifications_uuid,
            classification=classification_name,
            classification_choice=classification_choice_name,
        )

        p_finding_classifications.patient_finding_classification_choices.append(
            p_finding_classification_choice
        )

        return p_finding_classification_choice

    def create_classification_choice_descriptor(
        self,
        patient_examination: PExamination | str,
        patient_finding_classification_choice: PFindingClassificationChoice | str,
        classification_choice_descriptor: ClassificationChoiceDescriptor | str,
        descriptor_data: Dict[str, Any],  # TODO
    ) -> None:
        if isinstance(patient_examination, PExamination):
            p_examination_uuid = str(patient_examination.uuid)
        else:
            p_examination_uuid = patient_examination

        p_examination = self.ledger.patient_examinations[p_examination_uuid]

        if isinstance(
            patient_finding_classification_choice, PFindingClassificationChoice
        ):
            p_finding_classification_choice_uuid = str(
                patient_finding_classification_choice.uuid
            )
        else:
            p_finding_classification_choice_uuid = patient_finding_classification_choice

        if isinstance(classification_choice_descriptor, ClassificationChoiceDescriptor):
            classification_choice_descriptor_name = (
                classification_choice_descriptor.name
            )
        else:
            classification_choice_descriptor_name = classification_choice_descriptor

        _classification_choice_descriptor_obj = (
            self.knowledge_base.get_classification_choice_descriptor(
                classification_choice_descriptor_name
            )
        )

        p_finding_classification_choice_lookup_tuple = (
            p_examination.get_finding_classification_choice_by_uuid(
                p_finding_classification_choice_uuid
            )
        )

        _p_finding_classification_choice = (
            p_finding_classification_choice_lookup_tuple.p_finding_classification_choice
        )

        # TODO Finish implementation of descriptor creation
        raise NotImplementedError("Descriptor creation not yet implemented.")
