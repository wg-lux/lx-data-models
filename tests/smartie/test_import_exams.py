from pathlib import Path

import pytest

from lx_dtypes.utils.importer.smartie.schema import (
    SmartieExaminationSchema,
)

pytestmark = pytest.mark.localfiles

DATA_DIR = Path("./data/smartie")
FILENAME_EXAMS_ITT = DATA_DIR / "exams_itt_clean.csv"
FILENAME_EXAMS_PP = DATA_DIR / "exams_pp_clean.csv"
FILENAME_POLYPS_ITT = DATA_DIR / "polyps_itt_clean.csv"
FILENAME_POLYPS_PP = DATA_DIR / "polyps_pp_clean.csv"


class TestImportExams:
    def test_import_exams(self):
        exams_itt = SmartieExaminationSchema.load_csv(str(FILENAME_EXAMS_ITT))
        exams_pp = SmartieExaminationSchema.load_csv(str(FILENAME_EXAMS_PP))

        assert len(exams_itt.examinations) > 0
        assert len(exams_pp.examinations) > 0

        _exams_itt_ledger = exams_itt.create_ledger(name="SmartieExamsITT")
        _exams_pp_ledger = exams_pp.create_ledger(name="SmartieExamsPP")
