from typing import Dict, List


def str_unknown_factory() -> str:
    return "unknown"


def uuid_factory() -> str:
    """Generate a UUID string."""
    import uuid

    return str(uuid.uuid4())


def list_of_str_factory() -> List[str]:
    _list: List[str] = []
    return _list


def information_source_type_by_name_factory():
    from lx_dtypes.models.core.information_source import InformationSourceType

    _dict: Dict[str, InformationSourceType] = {}
    return _dict


def classification_by_name_factory():
    from lx_dtypes.models.core.classification import Classification

    _dict: Dict[str, Classification] = {}
    return _dict


def classification_type_by_name_factory():
    from lx_dtypes.models.core.classification import ClassificationType

    _dict: Dict[str, ClassificationType] = {}
    return _dict


def finding_type_by_name_factory():
    from lx_dtypes.models.core.finding import FindingType

    _dict: Dict[str, FindingType] = {}
    return _dict


def indication_by_name_factory():
    from lx_dtypes.models.core.indication import Indication

    _dict: Dict[str, Indication] = {}
    return _dict


def indication_type_by_name_factory():
    from lx_dtypes.models.core.indication import IndicationType

    _dict: Dict[str, IndicationType] = {}
    return _dict
