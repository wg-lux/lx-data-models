from typing import TYPE_CHECKING, Dict, List, Literal

if TYPE_CHECKING:
    from lx_dtypes.models.core.classification import Classification, ClassificationType
    from lx_dtypes.models.core.classification_choice_descriptor import (
        ClassificationChoiceDescriptor,
    )
    from lx_dtypes.models.core.finding import FindingType
    from lx_dtypes.models.core.indication import Indication, IndicationType
    from lx_dtypes.models.core.information_source import InformationSourceType
    from lx_dtypes.models.core.intervention import Intervention, InterventionType
    from lx_dtypes.models.core.unit import UnitType
    from lx_dtypes.models.examiner.examiner import Examiner
    from lx_dtypes.models.patient.patient_classification_choice_descriptor import (
        PatientFindingClassificationChoiceDescriptor,
    )
    from lx_dtypes.models.patient.patient_finding import PatientFinding
    from lx_dtypes.models.patient.patient_finding_classification_choice import (
        PatientFindingClassificationChoice,
    )
    from lx_dtypes.models.patient.patient_finding_classifications import (
        PatientFindingClassifications,
    )
    from lx_dtypes.models.patient.patient_indication import PatientIndication


def str_unknown_factory() -> Literal["unknown"]:
    return "unknown"


def uuid_factory() -> str:
    """Generate a UUID string."""
    import uuid

    return str(uuid.uuid4())


def list_of_str_factory() -> List[str]:
    _list: List[str] = []
    return _list


def list_of_unit_types_factory() -> List["UnitType"]:
    _list: List["UnitType"] = []
    return _list


def list_of_patient_indication_factory() -> List["PatientIndication"]:
    _list: List["PatientIndication"] = []
    return _list


def list_of_patient_finding_factory() -> List["PatientFinding"]:
    _list: List["PatientFinding"] = []
    return _list


def list_of_examiner_factory() -> List["Examiner"]:
    _list: List["Examiner"] = []
    return _list


def list_of_intervention_factory() -> List["Intervention"]:
    _list: List["Intervention"] = []
    return _list


def list_of_intervention_type_factory() -> List["InterventionType"]:
    _list: List["InterventionType"] = []
    return _list


def list_of_classification_choice_descriptor_factory() -> List[
    "ClassificationChoiceDescriptor"
]:
    _list: List["ClassificationChoiceDescriptor"] = []
    return _list


def list_of_patient_finding_classification_choice_descriptor_factory() -> List[
    "PatientFindingClassificationChoiceDescriptor"
]:
    _list: List["PatientFindingClassificationChoiceDescriptor"] = []
    return _list


def list_of_patient_finding_classifications_factory() -> List[
    "PatientFindingClassifications"
]:
    _list: List["PatientFindingClassifications"] = []
    return _list


def list_of_patient_finding_classification_choice_factory() -> List[
    "PatientFindingClassificationChoice"
]:
    _list: List["PatientFindingClassificationChoice"] = []
    return _list


def information_source_type_by_name_factory() -> Dict[str, "InformationSourceType"]:
    _dict: Dict[str, "InformationSourceType"] = {}
    return _dict


def classification_by_name_factory() -> Dict[str, "Classification"]:
    _dict: Dict[str, "Classification"] = {}
    return _dict


def classification_type_by_name_factory() -> Dict[str, "ClassificationType"]:
    _dict: Dict[str, "ClassificationType"] = {}
    return _dict


def finding_type_by_name_factory() -> Dict[str, "FindingType"]:
    _dict: Dict[str, "FindingType"] = {}
    return _dict


def indication_by_name_factory() -> Dict[str, "Indication"]:
    _dict: Dict[str, "Indication"] = {}
    return _dict


def indication_type_by_name_factory() -> Dict[str, "IndicationType"]:
    _dict: Dict[str, "IndicationType"] = {}
    return _dict


def intervention_by_name_factory() -> Dict[str, "Intervention"]:
    _dict: Dict[str, "Intervention"] = {}
    return _dict


def examiner_by_uuid_factory() -> Dict[str, "Examiner"]:
    _dict: Dict[str, "Examiner"] = {}
    return _dict
