from typing import List, Union

from lx_dtypes.models.base_models.base_model import AppBaseModel
from lx_dtypes.models.knowledge_base import KnowledgeBase
from lx_dtypes.models.ledger.patient import Patient
from lx_dtypes.models.ledger.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptor,
)
from lx_dtypes.models.ledger.patient_examination import PatientExamination
from lx_dtypes.models.ledger.patient_finding import PatientFinding
from lx_dtypes.models.ledger.patient_finding_classification_choice import (
    PatientFindingClassificationChoice,
)
from lx_dtypes.models.ledger.patient_ledger import PatientLedger

from .patient_interface_create import (
    create_examination_finding,
    create_patient_examination,
)
from .patient_interface_update import (
    add_classification_choice_to_finding,
    add_indication_to_examination,
)
from .patient_interface_utils import (
    patient_interface_classification_choice_exists,
    patient_interface_classification_exists,
    patient_interface_examination_exists,
    patient_interface_finding_exists,
    patient_interface_indication_exists,
)


class PatientInterface(AppBaseModel):
    knowledge_base: KnowledgeBase
    patient_ledger: PatientLedger

    # Create Methods
    def create_patient_examination(
        self, patient_uuid: str, examination_name: str
    ) -> PatientExamination:
        return create_patient_examination(
            patient_interface=self,
            patient_uuid=patient_uuid,
            examination_name=examination_name,
        )

    def create_examination_finding(
        self, examination_uuid: str, finding_name: str
    ) -> PatientFinding:
        return create_examination_finding(
            patient_interface=self,
            examination_uuid=examination_uuid,
            finding_name=finding_name,
        )

    # Utility Methods
    def examination_exists(self, examination_name: str) -> bool:
        return patient_interface_examination_exists(self, examination_name)

    def finding_exists(self, finding_name: str) -> bool:
        return patient_interface_finding_exists(self, finding_name)

    def classification_exists(self, classification_name: str) -> bool:
        return patient_interface_classification_exists(self, classification_name)

    def classification_choice_exists(self, choice_name: str) -> bool:
        return patient_interface_classification_choice_exists(self, choice_name)

    def indication_exists(self, indication_name: str) -> bool:
        return patient_interface_indication_exists(self, indication_name)

    # Get Methods
    def get_patient_by_uuid(self, patient_uuid: str) -> Patient:
        patient = self.patient_ledger.get_patient_by_uuid(patient_uuid)
        return patient

    def get_patient_examination_by_uuid(
        self, examination_uuid: str
    ) -> PatientExamination:
        examination = self.patient_ledger.get_examination_by_uuid(examination_uuid)
        return examination

    def get_patient_finding_by_patient_examination_and_finding_uuid(
        self, examination_uuid: str, finding_uuid: str
    ) -> PatientFinding:
        examination = self.get_patient_examination_by_uuid(examination_uuid)
        finding = examination.get_finding_by_uuid(finding_uuid)
        return finding

    # Update Methods
    def add_classification_choice_to_finding(
        self,
        examination_uuid: str,
        finding_uuid: str,
        classification_name: str,
        choice_name: str,
    ) -> PatientFindingClassificationChoice:
        return add_classification_choice_to_finding(
            patient_interface=self,
            examination_uuid=examination_uuid,
            finding_uuid=finding_uuid,
            classification_name=classification_name,
            choice_name=choice_name,
        )

    def add_indication_to_examination(
        self,
        examination_uuid: str,
        indication_name: str,
    ) -> PatientExamination:
        return add_indication_to_examination(
            patient_interface=self,
            examination_uuid=examination_uuid,
            indication_name=indication_name,
        )

    def add_descriptor_to_classification_choice(
        self,
        descriptor_name: str,
        examination_uuid: str,
        finding_uuid: str,
        choice_uuid: str,
        descriptor_value: Union[str, int, float, bool, List[str]],
    ) -> PatientFindingClassificationChoiceDescriptor:
        # examination = self.get_patient_examination_by_uuid(examination_uuid)
        finding = self.get_patient_finding_by_patient_examination_and_finding_uuid(
            examination_uuid, finding_uuid
        )
        finding_classifications = finding.get_or_create_classifications()
        choice = finding_classifications.get_choice_by_uuid(choice_uuid)
        kb_choice = self.knowledge_base.get_classification_choice(choice.choice_name)

        valid_descriptors = kb_choice.classification_choice_descriptor_names
        if descriptor_name not in valid_descriptors:
            raise ValueError(
                f"Descriptor '{descriptor_name}' is not valid for choice '{choice.choice_name}'. Valid descriptors are: {valid_descriptors}"
            )

        kb_descriptor = self.knowledge_base.get_classification_choice_descriptor(
            descriptor_name
        )
        descriptor_type = kb_descriptor.descriptor_type

        if descriptor_type == "numeric":
            if not isinstance(descriptor_value, (int, float)):
                raise ValueError(
                    f"Descriptor '{descriptor_name}' requires a numeric value."
                )
        elif descriptor_type == "text":
            if not isinstance(descriptor_value, str):
                raise ValueError(
                    f"Descriptor '{descriptor_name}' requires a string value."
                )
        elif descriptor_type == "boolean":
            if not isinstance(descriptor_value, bool):
                raise ValueError(
                    f"Descriptor '{descriptor_name}' requires a boolean value."
                )
        elif descriptor_type == "selection":
            if not isinstance(descriptor_value, list):
                raise ValueError(
                    f"Descriptor '{descriptor_name}' requires a list of selections."
                )
            else:
                valid_options = kb_descriptor.selection_options
                selection_multiple = kb_descriptor.selection_multiple
                selection_multiple_n_max = kb_descriptor.selection_multiple_n_max
                selection_multiple_n_min = kb_descriptor.selection_multiple_n_min
                if not selection_multiple and len(descriptor_value) > 1:
                    raise ValueError(
                        f"Descriptor '{descriptor_name}' allows only a single selection."
                    )
                if len(descriptor_value) < selection_multiple_n_min:
                    raise ValueError(
                        f"Descriptor '{descriptor_name}' requires at least {selection_multiple_n_min} selections."
                    )
                if len(descriptor_value) > selection_multiple_n_max:
                    raise ValueError(
                        f"Descriptor '{descriptor_name}' allows at most {selection_multiple_n_max} selections."
                    )

                for option in descriptor_value:
                    if option not in valid_options:
                        raise ValueError(
                            f"Option '{option}' is not valid for descriptor '{descriptor_name}'. Valid options are: {valid_options}"
                        )
        _examination_uuid = finding.patient_examination_uuid
        assert _examination_uuid == examination_uuid
        assert _examination_uuid is not None
        descriptor = PatientFindingClassificationChoiceDescriptor(
            descriptor_value=descriptor_value,
            patient_uuid=finding.patient_uuid,
            patient_examination_uuid=_examination_uuid,
            patient_finding_uuid=finding.uuid,
            patient_finding_classifications_uuid=finding_classifications.uuid,
            patient_finding_classification_choice_uuid=choice.uuid,
            descriptor_name=descriptor_name,
        )
        choice.descriptors.append(descriptor)
        return descriptor

    # Delete Methods
    def delete_examination(self, examination_uuid: str) -> None:
        self.patient_ledger.delete_patient_examination(examination_uuid)

    def delete_patient(self, patient_uuid: str) -> None:
        self.patient_ledger.delete_patient(patient_uuid)

    def delete_finding_from_examination(
        self, examination_uuid: str, finding_uuid: str
    ) -> None:
        examination = self.get_patient_examination_by_uuid(examination_uuid)
        examination.delete_finding(finding_uuid)

    def delete_classification_choice_from_finding(
        self,
        examination_uuid: str,
        finding_uuid: str,
        choice_uuid: str,
    ) -> None:
        examination = self.get_patient_examination_by_uuid(examination_uuid)
        finding = examination.get_finding_by_uuid(finding_uuid)
        finding.delete_classification_choice(choice_uuid)

    def delete_indication_from_examination(
        self,
        examination_uuid: str,
        indication_uuid: str,
    ) -> None:
        examination = self.get_patient_examination_by_uuid(examination_uuid)
        examination.delete_indication(indication_uuid)
