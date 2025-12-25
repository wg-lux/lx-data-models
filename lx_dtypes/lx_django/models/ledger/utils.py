import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict


if TYPE_CHECKING:
    from lx_dtypes.lx_django.models.core.classification import Classification
    from lx_dtypes.lx_django.models.core.classification_choice import (
        ClassificationChoice,
    )
    from lx_dtypes.lx_django.models.core.classification_choice_descriptor import (
        ClassificationChoiceDescriptor,
    )
    from lx_dtypes.lx_django.models.core.examination import Examination
    from lx_dtypes.lx_django.models.core.finding import Finding
    from lx_dtypes.lx_django.models.core.indication import Indication
    from lx_dtypes.lx_django.models.core.intervention import Intervention
    from lx_dtypes.lx_django.models.ledger.patient import Patient
    from lx_dtypes.lx_django.models.ledger.patient_examination import (
        PatientExamination,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding import (
        PatientFinding,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_classification_choice import (
        PatientFindingClassificationChoice,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_classification_choice_descriptor import (
        PatientFindingClassificationChoiceDescriptor,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_classifications import (
        PatientFindingClassifications,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_intervention import (
        PatientFindingIntervention,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_interventions import (
        PatientFindingInterventions,
    )
    from lx_dtypes.lx_django.models.ledger.patient_indication import (
        PatientIndication,
    )


class LedgerInstancesFromDDict(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    patient: Optional["Patient"] = None
    examination: Optional["PatientExamination"] = None
    finding: Optional["PatientFinding"] = None
    findings: Optional[List["PatientFinding"]] = None
    classifications: Optional["PatientFindingClassifications"] = None
    classification_choice: Optional["PatientFindingClassificationChoice"] = None
    classification_choices: Optional[List["PatientFindingClassificationChoice"]] = None
    classification_choice_descriptor: Optional[
        "PatientFindingClassificationChoiceDescriptor"
    ] = None
    classification_choice_descriptors: Optional[
        List["PatientFindingClassificationChoiceDescriptor"]
    ] = None
    indication: Optional["PatientIndication"] = None
    indications: Optional[List["PatientIndication"]] = None
    interventions: Optional["PatientFindingInterventions"] = None
    intervention: Optional["PatientFindingIntervention"] = None
    intervention_list: Optional[List["PatientFindingIntervention"]] = None


def transform_uuid_fields(
    model_dict: Dict[str, Any],
    patient: bool = False,
    examination: bool = False,
    indication: bool = False,
    indications: bool = False,
    finding: bool = False,
    findings: bool = False,
    classifications: bool = False,
    classification_choice: bool = False,
    classification_choices: bool = False,
    classification_choice_descriptor: bool = False,
    classification_choice_descriptors: bool = False,
    interventions: bool = False,
    intervention: bool = False,
    intervention_list: bool = False,
) -> Tuple[Dict[str, Any], LedgerInstancesFromDDict]:
    from lx_dtypes.lx_django.models.ledger.patient import Patient
    from lx_dtypes.lx_django.models.ledger.patient_examination import (
        PatientExamination,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding import (
        PatientFinding,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_classification_choice import (
        PatientFindingClassificationChoice,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_classification_choice_descriptor import (
        PatientFindingClassificationChoiceDescriptor,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_classifications import (
        PatientFindingClassifications,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_intervention import (
        PatientFindingIntervention,
    )
    from lx_dtypes.lx_django.models.ledger.patient_finding_interventions import (
        PatientFindingInterventions,
    )
    from lx_dtypes.lx_django.models.ledger.patient_indication import (
        PatientIndication,
    )

    instances = LedgerInstancesFromDDict()

    # Patient
    patient_uuid: uuid.UUID | None = model_dict.pop("patient_uuid", None)
    if patient_uuid and patient:
        instances.patient = Patient.objects.get(uuid=patient_uuid)

    # Examination
    examination_uuid: uuid.UUID | None = model_dict.pop(
        "patient_examination_uuid", None
    )
    if examination_uuid and examination:
        instances.examination = PatientExamination.objects.get(uuid=examination_uuid)

    # indications
    indication_uuids: List[uuid.UUID] | None = model_dict.pop(
        "patient_indications_uuids", None
    )
    indication_uuid: uuid.UUID | None = model_dict.pop("patient_indication_uuid", None)

    if indication_uuids and indications:
        indication_instances = PatientIndication.objects.filter(
            uuid__in=indication_uuids
        )
        instances.indications = list(indication_instances)

    if indication_uuid and indication:
        instances.indication = PatientIndication.objects.get(uuid=indication_uuid)

    # Finding
    finding_uuid: uuid.UUID | None = model_dict.pop("patient_finding_uuid", None)
    finding_uuids: List[uuid.UUID] | None = model_dict.pop(
        "patient_findings_uuids", None
    )

    if finding_uuid and finding:
        instances.finding = PatientFinding.objects.get(uuid=finding_uuid)

    if finding_uuids and findings:
        finding_instances = PatientFinding.objects.filter(uuid__in=finding_uuids)
        instances.findings = list(finding_instances)

    # Classification
    classifications_uuid: uuid.UUID | None = model_dict.pop(
        "patient_finding_classifications_uuid", None
    )
    if classifications_uuid and classifications:
        instances.classifications = PatientFindingClassifications.objects.get(
            uuid=classifications_uuid
        )

    classification_choice_uuid: uuid.UUID | None = model_dict.pop(
        "patient_finding_classification_choice_uuid", None
    )

    if classification_choice_uuid and classification_choice:
        instances.classification_choice = (
            PatientFindingClassificationChoice.objects.get(
                uuid=classification_choice_uuid
            )
        )

    classification_choice_uuids: List[uuid.UUID] | None = model_dict.pop(
        "patient_finding_classification_choices_uuids", None
    )

    if classification_choice_uuids and classification_choices:
        classification_choice_instances = (
            PatientFindingClassificationChoice.objects.filter(
                uuid__in=classification_choice_uuids
            )
        )
        instances.classification_choices = list(classification_choice_instances)

    # Descriptor
    classification_choice_descriptor_uuid: uuid.UUID | None = model_dict.pop(
        "patient_finding_classification_choice_descriptor_uuid", None
    )
    if classification_choice_descriptor_uuid and classification_choice_descriptor:
        instances.classification_choice_descriptor = (
            PatientFindingClassificationChoiceDescriptor.objects.get(
                uuid=classification_choice_descriptor_uuid
            )
        )
    classification_choice_descriptor_uuids: List[uuid.UUID] | None = model_dict.pop(
        "patient_finding_classification_choice_descriptors_uuids", None
    )

    if classification_choice_descriptor_uuids and classification_choice_descriptors:
        descriptor_instances = (
            PatientFindingClassificationChoiceDescriptor.objects.filter(
                uuid__in=classification_choice_descriptor_uuids
            )
        )
        instances.classification_choice_descriptors = list(descriptor_instances)

    # Interventions
    interventions_uuid: uuid.UUID | None = model_dict.pop(
        "patient_finding_interventions_uuid", None
    )
    intervention_uuid: uuid.UUID | None = model_dict.pop(
        "patient_finding_intervention_uuid", None
    )
    intervention_uuids: List[uuid.UUID] | None = model_dict.pop(
        "patient_finding_interventions_uuids", None
    )

    if interventions_uuid and interventions:
        instances.interventions = PatientFindingInterventions.objects.get(
            uuid=interventions_uuid
        )
    if intervention_uuid and intervention:
        instances.intervention = PatientFindingIntervention.objects.get(
            uuid=intervention_uuid
        )

    if intervention_uuids and intervention_list:
        intervention_instances = PatientFindingIntervention.objects.filter(
            uuid__in=intervention_uuids
        )
        instances.intervention_list = list(intervention_instances)

    return model_dict, instances


class KbInstancesFromDDict(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    examination: Optional["Examination"] = None
    finding: Optional["Finding"] = None
    indication: Optional["Indication"] = None
    intervention: Optional["Intervention"] = None
    classification: Optional["Classification"] = None
    classification_choice: Optional["ClassificationChoice"] = None
    classification_choice_descriptor: Optional["ClassificationChoiceDescriptor"] = None


def transform_kb_name_fields(
    model_dict: Dict[str, Any],
    examination: bool = False,
    finding: bool = False,
    indication: bool = False,
    intervention: bool = False,
    classification: bool = False,
    classification_choice: bool = False,
    classification_choice_descriptor: bool = False,
) -> Tuple[Dict[str, Any], KbInstancesFromDDict]:
    from lx_dtypes.lx_django.models.core.classification import Classification
    from lx_dtypes.lx_django.models.core.classification_choice import (
        ClassificationChoice,
    )
    from lx_dtypes.lx_django.models.core.classification_choice_descriptor import (
        ClassificationChoiceDescriptor,
    )
    from lx_dtypes.lx_django.models.core.examination import Examination
    from lx_dtypes.lx_django.models.core.finding import Finding
    from lx_dtypes.lx_django.models.core.indication import Indication
    from lx_dtypes.lx_django.models.core.intervention import Intervention

    instances = KbInstancesFromDDict()

    examination_name = model_dict.pop("examination_name", None)
    finding_name = model_dict.pop("finding_name", None)
    indication_name = model_dict.pop("indication_name", None)
    intervention_name = model_dict.pop("intervention_name", None)
    classification_name = model_dict.pop("classification_name", None)
    classification_choice_name = model_dict.pop("choice_name", None)
    classification_choice_descriptor_name = model_dict.pop(
        "classification_choice_descriptor_name", None
    )

    if examination_name and examination:
        instances.examination = Examination.get_by_name(examination_name)
    if finding_name and finding:
        instances.finding = Finding.get_by_name(finding_name)
    if indication_name and indication:
        instances.indication = Indication.get_by_name(indication_name)
    if intervention_name and intervention:
        instances.intervention = Intervention.get_by_name(intervention_name)
    if classification_name and classification:
        instances.classification = Classification.get_by_name(classification_name)
    if classification_choice_name and classification_choice:
        instances.classification_choice = ClassificationChoice.get_by_name(
            classification_choice_name
        )
    if classification_choice_descriptor_name and classification_choice_descriptor:
        instances.classification_choice_descriptor = (
            ClassificationChoiceDescriptor.get_by_name(
                classification_choice_descriptor_name
            )
        )

    return model_dict, instances
