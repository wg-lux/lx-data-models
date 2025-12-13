from typing import TYPE_CHECKING, List, Literal, Optional, Tuple

from lx_dtypes.models.patient.patient_finding import PatientFinding
from lx_dtypes.models.patient_interface.main import PatientInterface
from lx_dtypes.utils.importer.smartie.names import (
    SMARTIE_CLASSIFICATION_CHOICE_ENUM,
    SMARTIE_CLASSIFICATION_ENUM,
    SMARTIE_DESCRIPTOR_ENUM,
    SMARTIE_FINDING_ENUM,
)

if TYPE_CHECKING:
    from lx_dtypes.utils.importer.smartie.schema import SmartieExaminationSchema


def smartie_map_gender(gender: int) -> Literal["male", "female", "unknown"]:
    """Map Smartie gender integer to string representation.
    Args:
        gender (int): Smartie gender, where 0 = male, 1 = female
    Returns:
        Literal["male","female","unknown"]: Mapped gender string.

    """
    if gender == 0:
        return "male"
    elif gender == 1:
        return "female"
    else:
        return "unknown"


def smartie_exam_map_sedation(
    exam: "SmartieExaminationSchema",
    record_uuid: str,
    patient_interface: PatientInterface,
) -> None:
    """
    Map sedation information from a Smartie examination record to patient findings.

    This function processes sedation data from an examination, creates a sedation finding,
    and adds classifications for sedation performance and type.

    Args:
        exam (SmartieExaminationSchema): The examination object containing sedation data.
        record_uuid (str): The UUID identifier for the examination record.
        patient_interface (PatientInterface): Interface for creating and modifying patient findings.

    Returns:
        None

    Raises:
        ValueError: If sedation mapping fails due to unrecognized sedation types in the sedation list.

    Notes:
        - Filters out empty strings and "no" values from the sedation list.
        - If no valid sedation is found, marks sedation as not performed and returns early.
        - Supports sedation type classifications: propofol, midazolam, propofol + midazolam, other, or unknown.
        - Creates two findings: SEDATION_PERFORMED (yes/no) and SEDATION (specific type).
    """
    sedation_list = exam.sedation
    # "remove 'no' from sedation list if present"
    sedation_list = [s for s in sedation_list if s and s.lower() != "no"]
    if len(sedation_list) == 0:
        sedation_performed_choice_name = SMARTIE_CLASSIFICATION_CHOICE_ENUM.NO.value
    else:
        sedation_performed_choice_name = SMARTIE_CLASSIFICATION_CHOICE_ENUM.YES.value

    ##### CREATE FINDING SEDATION PERFORMED #####
    finding_name = SMARTIE_FINDING_ENUM.SEDATION.value
    finding_classification_name = SMARTIE_CLASSIFICATION_ENUM.SEDATION_PERFORMED.value

    finding = patient_interface.create_examination_finding(
        examination_uuid=record_uuid,
        finding_name=finding_name,
    )

    _sedation_performed_choice = patient_interface.add_classification_choice_to_finding(
        examination_uuid=record_uuid,
        finding_uuid=finding.uuid,
        classification_name=finding_classification_name,
        choice_name=sedation_performed_choice_name,
    )

    if sedation_performed_choice_name == SMARTIE_CLASSIFICATION_CHOICE_ENUM.NO.value:
        return

    finding_classification_name = SMARTIE_CLASSIFICATION_ENUM.SEDATION.value

    if "other" in sedation_list:
        sedation_choice_name = SMARTIE_CLASSIFICATION_CHOICE_ENUM.SEDATION_OTHER.value

    elif "unknown" in sedation_list:
        sedation_choice_name = SMARTIE_CLASSIFICATION_CHOICE_ENUM.SEDATION_OTHER.value
    elif "propofol" in sedation_list and "midazolam" in sedation_list:
        sedation_choice_name = (
            SMARTIE_CLASSIFICATION_CHOICE_ENUM.SEDATION_PROPOFOL_MIDAZOLAM.value
        )
    elif "propofol" in sedation_list:
        sedation_choice_name = (
            SMARTIE_CLASSIFICATION_CHOICE_ENUM.SEDATION_PROPOFOL.value
        )
    elif "midazolam" in sedation_list:
        sedation_choice_name = (
            SMARTIE_CLASSIFICATION_CHOICE_ENUM.SEDATION_MIDAZOLAM.value
        )
    else:
        raise ValueError(
            f"Sedation mapping error for exam record_id {exam.record_id} with sedation list {sedation_list}."
        )

    _sedation_generic_choice = patient_interface.add_classification_choice_to_finding(
        examination_uuid=record_uuid,
        finding_uuid=finding.uuid,
        classification_name=finding_classification_name,
        choice_name=sedation_choice_name,
    )

    return


###############


def smartie_exam_map_hardware(
    exam: "SmartieExaminationSchema",
    record_uuid: str,
    patient_interface: PatientInterface,
) -> None:
    """Map hardware findings from Smartie exam to patient interface.

    Args:
        exam (SmartieExaminationSchema): The Smartie examination data.
        record_uuid (str): The UUID of the patient examination record.
        patient_interface (PatientInterface): The patient interface to add findings to.
    """
    processor_model = exam.processor
    if not processor_model:
        return

    finding_name = SMARTIE_FINDING_ENUM.ENDOSCOPY_HARDWARE_USED.value
    classification_name = SMARTIE_CLASSIFICATION_ENUM.HARDWARE_ENDOSCOPE_PROCESSOR.value

    if processor_model == "Storz Image 1 S":
        classification_value = (
            SMARTIE_CLASSIFICATION_CHOICE_ENUM.HARDWARE_ENDOSCOPE_STORZ.value
        )
    elif processor_model == "Pentax EPK i7000":
        classification_value = (
            SMARTIE_CLASSIFICATION_CHOICE_ENUM.HARDWARE_ENDOSCOPE_PENTAX.value
        )
    elif processor_model == "Olympus CV-170":
        classification_value = (
            SMARTIE_CLASSIFICATION_CHOICE_ENUM.HARDWARE_ENDOSCOPE_OLYMPUS_170.value
        )
    elif processor_model == "Olympus CV-190":
        classification_value = (
            SMARTIE_CLASSIFICATION_CHOICE_ENUM.HARDWARE_ENDOSCOPE_OLYMPUS_190.value
        )
    else:
        raise ValueError(f"Unknown processor model: {processor_model}")

    finding = patient_interface.create_examination_finding(
        examination_uuid=record_uuid,
        finding_name=finding_name,
    )

    patient_interface.add_classification_choice_to_finding(
        examination_uuid=record_uuid,
        finding_uuid=finding.uuid,
        classification_name=classification_name,
        choice_name=classification_value,
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


def smartie_exam_map_bbps(
    exam: "SmartieExaminationSchema",
    patient_interface: PatientInterface,
    record_uuid: str,
) -> None:
    """ """
    bbps_simplified_value = exam.bbps_worst
    bbps_individual = exam.bbps

    smartie_validate_bbps_input(
        bbps_simplified_value=bbps_simplified_value,
        bbps_individual=bbps_individual,
    )

    if bbps_simplified_value is not None:
        smartie_map_bbps_simplified(
            bbps_value=bbps_simplified_value,
            patient_interface=patient_interface,
            examination_uuid=record_uuid,
        )


#### WITHDRAWAL TIME #######
def smartie_exam_map_withdrawal_time(
    exam: "SmartieExaminationSchema",
    patient_interface: PatientInterface,
    record_uuid: str,
) -> None:
    """ """
    withdrawal_time = exam.withdrawal_time
    if withdrawal_time is None or withdrawal_time < 0:
        return

    finding_name = SMARTIE_FINDING_ENUM.WITHDRAWAL_TIME_MINUTES.value
    classification_name = SMARTIE_CLASSIFICATION_ENUM.TIME_MINUTES_GENERIC.value
    choice_name = SMARTIE_CLASSIFICATION_CHOICE_ENUM.MINUTES_NUMERIC.value
    descriptor_name = SMARTIE_DESCRIPTOR_ENUM.TIME_MINUTES_NUMERIC.value

    finding = patient_interface.create_examination_finding(
        examination_uuid=record_uuid,
        finding_name=finding_name,
    )

    wt_classification_choice = patient_interface.add_classification_choice_to_finding(
        examination_uuid=record_uuid,
        finding_uuid=finding.uuid,
        classification_name=classification_name,
        choice_name=choice_name,
    )

    _wt_descriptor = patient_interface.add_descriptor_to_classification_choice(
        descriptor_name=descriptor_name,
        examination_uuid=record_uuid,
        finding_uuid=finding.uuid,
        choice_uuid=wt_classification_choice.uuid,
        descriptor_value=withdrawal_time,
    )
