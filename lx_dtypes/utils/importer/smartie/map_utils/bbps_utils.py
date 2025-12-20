from typing import List, Optional, Tuple

from lx_dtypes.models.ledger.patient_finding import PatientFinding
from lx_dtypes.models.patient_interface.main import PatientInterface
from lx_dtypes.utils.importer.smartie.names import (
    SMARTIE_CLASSIFICATION_CHOICE_ENUM,
    SMARTIE_CLASSIFICATION_ENUM,
    SMARTIE_FINDING_ENUM,
)


######### BBPS #########
def smartie_validate_bbps_input(
    bbps_simplified_value: Optional[int] = None,
    bbps_individual: Optional[Tuple[int, int, int]] = None,
) -> None:
    _simplified_available = bbps_simplified_value is not None
    if _simplified_available:
        assert isinstance(bbps_simplified_value, int)
        # assert in 0-3
        assert 0 <= bbps_simplified_value <= 3

    _individual_available = bbps_individual is not None
    if _individual_available:
        _lowest = 3
        _total = 0
        assert isinstance(bbps_individual, tuple)
        assert len(bbps_individual) == 3
        for score in bbps_individual:
            assert 0 <= score <= 3
            if score < _lowest:
                _lowest = score
            _total += score
        # cross check with simplified and total
        if _simplified_available:
            assert bbps_simplified_value == _lowest


def smartie_map_bbps_choice(bbps_value: int) -> str:
    if bbps_value == 0:
        return SMARTIE_CLASSIFICATION_CHOICE_ENUM.BBPS_0.value
    elif bbps_value == 1:
        return SMARTIE_CLASSIFICATION_CHOICE_ENUM.BBPS_1.value
    elif bbps_value == 2:
        return SMARTIE_CLASSIFICATION_CHOICE_ENUM.BBPS_2.value
    elif bbps_value == 3:
        return SMARTIE_CLASSIFICATION_CHOICE_ENUM.BBPS_3.value
    else:
        raise ValueError(f"Invalid BBPS simplified value: {bbps_value}")


def smartie_map_bbps_simplified(
    bbps_value: int,
    patient_interface: PatientInterface,
    examination_uuid: str,
) -> None:
    finding_name = SMARTIE_FINDING_ENUM.BP_SIMPLIFIED.value
    classification_name = SMARTIE_CLASSIFICATION_ENUM.BBPS_SIMPLIFIED.value
    choice_name = smartie_map_bbps_choice(bbps_value)

    finding_uuid = patient_interface.create_examination_finding(
        examination_uuid=examination_uuid,
        finding_name=finding_name,
    ).uuid

    patient_interface.add_classification_choice_to_finding(
        examination_uuid=examination_uuid,
        finding_uuid=finding_uuid,
        classification_name=classification_name,
        choice_name=choice_name,
    )


def smartie_map_bbps_individual(
    bbps_values: Tuple[int, int, int],
    patient_interface: PatientInterface,
    examination_uuid: str,
) -> None:
    """bbps values are expected to be ordered (left, transverse, right)"""
    finding_name_bp_lc = SMARTIE_FINDING_ENUM.BP_LC.value
    finding_name_bp_tc = SMARTIE_FINDING_ENUM.BP_TC.value
    finding_name_bp_rc = SMARTIE_FINDING_ENUM.BP_RC.value

    finding_names = [
        finding_name_bp_lc,
        finding_name_bp_tc,
        finding_name_bp_rc,
    ]

    findings: List[PatientFinding] = []
    for idx, segment_value in enumerate(bbps_values):
        finding = patient_interface.create_examination_finding(
            examination_uuid=examination_uuid,
            finding_name=finding_names[idx],
        )
        findings.append(finding)

        classification_name = SMARTIE_CLASSIFICATION_ENUM.BBPS.value
        choice_name = smartie_map_bbps_choice(segment_value)

        patient_interface.add_classification_choice_to_finding(
            examination_uuid=examination_uuid,
            finding_uuid=finding.uuid,
            classification_name=classification_name,
            choice_name=choice_name,
        )
