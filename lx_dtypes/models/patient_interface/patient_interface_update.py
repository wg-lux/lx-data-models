from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lx_dtypes.models.patient.patient_examination import PatientExamination
    from lx_dtypes.models.patient.patient_finding_classification_choice import (
        PatientFindingClassificationChoice,
    )
    from lx_dtypes.models.patient_interface import PatientInterface


def add_classification_choice_to_finding(
    patient_interface: "PatientInterface",
    examination_uuid: str,
    finding_uuid: str,
    classification_name: str,
    choice_name: str,
) -> "PatientFindingClassificationChoice":
    from lx_dtypes.models.patient.patient_finding_classification_choice import (
        PatientFindingClassificationChoice,
    )

    if not patient_interface.classification_exists(classification_name):
        raise ValueError(
            f"Classification '{classification_name}' does not exist in the knowledge base."
        )

    if not patient_interface.classification_choice_exists(choice_name):
        raise ValueError(
            f"Classification choice '{choice_name}' does not exist in the knowledge base."
        )

    classification_object = patient_interface.knowledge_base.get_classification(
        classification_name
    )
    valid_choices = classification_object.choice_names

    if choice_name not in valid_choices:
        raise ValueError(
            f"Choice '{choice_name}' is not a valid choice for classification '{classification_name}'. Valid choices are: {valid_choices}"
        )

    patient_finding = (
        patient_interface.get_patient_finding_by_patient_examination_and_finding_uuid(
            examination_uuid, finding_uuid
        )
    )

    patient_finding_classifications = patient_finding.get_or_create_classifications()

    classification_choice = PatientFindingClassificationChoice.create(
        choice_name=choice_name,
        patient_uuid=patient_finding.patient_uuid,
        patient_examination_uuid=patient_finding.patient_examination_uuid,
        patient_finding_uuid=patient_finding.uuid,
        patient_finding_classifications_uuid=patient_finding_classifications.uuid,
        classification_name=classification_name,
    )
    patient_finding.add_classification_choice(classification_choice)

    return classification_choice


def add_indication_to_examination(
    patient_interface: "PatientInterface",
    examination_uuid: str,
    indication_name: str,
) -> "PatientExamination":
    if not patient_interface.indication_exists(indication_name):
        raise ValueError(
            f"Indication '{indication_name}' does not exist in the knowledge base."
        )

    # get the patient examination
    patient_examination = patient_interface.get_patient_examination_by_uuid(
        examination_uuid
    )

    examination_name = patient_examination.examination_name

    kb_examination = patient_interface.knowledge_base.get_examination(examination_name)

    if indication_name not in kb_examination.indication_names:
        raise ValueError(
            f"Indication '{indication_name}' is not valid for examination '{examination_name}'."
        )

    patient_examination.create_indication(indication_name)
    return patient_examination
