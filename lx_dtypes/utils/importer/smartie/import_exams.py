from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List

from lx_dtypes.models.patient.patient_ledger import PatientLedger

from .names import OMIT_COLS_EXAMS

if TYPE_CHECKING:
    from lx_dtypes.utils.importer.smartie.schema import (
        SmartieExaminations,
        SmartieExaminationSchema,
    )


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
                row["birthdate"] = datetime.strptime(
                    row["birthdate"].split(" ")[0], "%Y-%m-%d"
                ).date()
            if "exam_date" in row:
                row["exam_date"] = datetime.strptime(
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
