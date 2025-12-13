import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List

from lx_dtypes.models.patient.patient_examination import (
    PatientExamination,
    # PatientExaminationDataDict,
)

# from lx_dtypes.models.patient.patient_finding import (
#     PatientFinding,
#     PatientFindingDataDict,
# )
from lx_dtypes.models.patient.patient_ledger import PatientLedger
from lx_dtypes.models.patient_interface.main import PatientInterface
from lx_dtypes.utils.importer.smartie.mappings import smartie_exam_map_sedation

# from .mappings import smartie_map_gender
from .names import (
    OMIT_COLS_EXAMS,
    SMARTIE_CLASSIFICATION_CHOICE_ENUM,
    SMARTIE_CLASSIFICATION_ENUM,
    SMARTIE_EXAMINATION_ENUM,
    SMARTIE_FINDING_ENUM,
)

if TYPE_CHECKING:
    from lx_dtypes.utils.importer.smartie.schema import (
        SmartieExaminations,
        SmartieExaminationSchema,
    )


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


def smartie_findings_exam_to_ledger(
    exam: "SmartieExaminationSchema",
    patient_interface: PatientInterface,
    record_uuid: str,
) -> None:
    """ """
    smartie_exam_map_sedation(
        exam=exam,
        record_uuid=record_uuid,
        patient_interface=patient_interface,
    )

    smartie_exam_map_hardware(
        exam=exam,
        record_uuid=record_uuid,
        patient_interface=patient_interface,
    )
    # smartie_exam_map_bbps()
    # smartie_exam_map_withdrawal_time()
    # smartie_exam_par_deepest_point()


def smartie_findings_exams_to_ledger(
    exams: List["SmartieExaminationSchema"],
    patient_interface: PatientInterface,
    person_id2uuid: dict[int, str],
    record_id2uuid: dict[int, str],
) -> None:
    for exam in exams:
        person_uuid = person_id2uuid.get(exam.person_id)
        record_uuid = record_id2uuid.get(exam.record_id)
        if person_uuid is None or record_uuid is None:
            raise ValueError(
                f"UUID mapping missing for person_id {exam.person_id} or record_id {exam.record_id}."
            )
        smartie_findings_exam_to_ledger(exam, patient_interface, record_uuid)


def smartie_exam_to_ledger(
    exam: "SmartieExaminationSchema",
    ledger: PatientLedger,
    record_uuid: str,
    person_uuid: str,
) -> None:
    examination_name = SMARTIE_EXAMINATION_ENUM.COLONOSCOPY.value
    exam_date = exam.exam_date
    # convert to timezone aware datetime
    exam_dt = datetime.datetime(
        year=exam_date.year,
        month=exam_date.month,
        day=exam_date.day,
        tzinfo=datetime.timezone.utc,
    )
    patient_examination = PatientExamination.create(
        patient_uuid=person_uuid,
        examination_uuid=record_uuid,
        examination_name=examination_name,
        date=exam_dt,
    )

    examination_indication_name = exam.std_indication
    _ = patient_examination.create_indication(
        indication_name=examination_indication_name
    )

    ledger.add_patient_examination(patient_examination)


def smartie_exams_to_ledger(
    exams: List["SmartieExaminationSchema"],
    ledger: PatientLedger,
    person_id2uuid: dict[int, str],
    record_id2uuid: dict[int, str],
) -> None:
    for exam in exams:
        person_uuid = person_id2uuid.get(exam.person_id)
        record_uuid = record_id2uuid.get(exam.record_id)
        if person_uuid is None or record_uuid is None:
            raise ValueError(
                f"UUID mapping missing for person_id {exam.person_id} or record_id {exam.record_id}."
            )
        smartie_exam_to_ledger(exam, ledger, record_uuid, person_uuid)


def smartie_patients_to_ledger(
    exams: List["SmartieExaminationSchema"],
    ledger: PatientLedger,
    person_id2uuid: dict[int, str],
) -> None:
    person_ids = set(person_id2uuid.keys())
    for exam in exams:
        if exam.person_id not in person_ids:
            continue
        smartie_patient_to_ledger(exam, ledger, person_id2uuid)
        person_ids.remove(exam.person_id)


def smartie_patient_to_ledger(
    exam: "SmartieExaminationSchema",
    ledger: PatientLedger,
    person_id2uuid: dict[int, str],
) -> None:
    assert person_id2uuid is not None
    new_uuid = person_id2uuid.get(exam.person_id)
    assert new_uuid is not None
    _, patient = exam.create_patient(new_uuid=new_uuid)
    assert _ == new_uuid
    ledger.add_patient(patient)


def load_smartie_exams_csv(
    filepath: str,
) -> "SmartieExaminations":
    """Load Smartie examinations from a CSV file.

    Args:
        filepath (str): Path to the CSV file containing Smartie examinations.
    """
    import csv

    from lx_dtypes.utils.importer.smartie.schema import (
        SmartieExaminations,
        SmartieExaminationSchema,
    )

    examinations: List["SmartieExaminationSchema"] = []

    _path = Path(filepath)
    _path = _path.expanduser().resolve()
    assert _path.exists(), f"File {filepath} does not exist."

    with open(_path.as_posix(), "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",")
        for row in reader:
            # remove_empty_string_fields
            record_id = row["record_id"]
            if record_id == "nan":
                continue
            fields = row.keys()
            _pop_fields: List[str] = []
            for _field in fields:
                if row[_field] == "" or row[_field] == "-1":
                    _pop_fields.append(_field)
            for _field in _pop_fields:
                row.pop(_field)

            # Preprocess certain fields
            if "birthdate" in row:
                row["birthdate"] = datetime.datetime.strptime(
                    row["birthdate"].split(" ")[0], "%Y-%m-%d"
                ).date()
            if "exam_date" in row:
                row["exam_date"] = datetime.datetime.strptime(
                    row["exam_date"].split(" ")[0], "%Y-%m-%d"
                ).date()
            if "sedation" in row:
                row["sedation"] = (
                    row["sedation"].strip("{}").split(",") if row["sedation"] else []
                )
            if "bbps" in row:
                row["bbps"] = (
                    tuple(int(x) for x in row["bbps"].strip("{}").split(","))
                    if row["bbps"]
                    else (0, 0, 0)
                )

            for col in OMIT_COLS_EXAMS:
                if col in row:
                    del row[col]
            examinations.append(SmartieExaminationSchema.model_validate(row))
    smartie_examinations = SmartieExaminations.model_validate(
        {"examinations": examinations}
    )
    return smartie_examinations
