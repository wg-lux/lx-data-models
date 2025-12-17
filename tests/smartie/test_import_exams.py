from pathlib import Path

# import pytest
from lx_dtypes.models.knowledge_base import KnowledgeBase
from lx_dtypes.models.patient_interface import PatientInterface
from lx_dtypes.stats.interface_export import interface2dataset
from lx_dtypes.utils.importer.smartie.schema import (
    SmartieExaminationSchema,
)

# pytestmark = pytest.mark.localfiles

DATA_DIR = Path("./data/smartie")
FILENAME_EXAMS_ITT = DATA_DIR / "exams_itt_clean.csv"
FILENAME_EXAMS_PP = DATA_DIR / "exams_pp_clean.csv"
FILENAME_POLYPS_ITT = DATA_DIR / "polyps_itt_clean.csv"
FILENAME_POLYPS_PP = DATA_DIR / "polyps_pp_clean.csv"

EXPORT_DIR = DATA_DIR / "exported"
EXPORT_DIR.mkdir(exist_ok=True)


class TestImportExams:
    def test_import_exams(self, lx_knowledge_base: KnowledgeBase):
        exams_itt = SmartieExaminationSchema.load_csv(str(FILENAME_EXAMS_ITT))
        assert len(exams_itt.examinations) > 0
        _exams_itt_ledger = exams_itt.create_ledger(name="SmartieExamsITT")
        interface_itt = PatientInterface(
            knowledge_base=lx_knowledge_base,
            patient_ledger=_exams_itt_ledger,
        )
        exams_itt.export_exam_findings_to_interface(interface_itt)

        dataset_itt = interface2dataset(interface_itt)
        dataset_itt.to_csvs(EXPORT_DIR / "interface_export_itt")

        exams_pp = SmartieExaminationSchema.load_csv(str(FILENAME_EXAMS_PP))
        assert len(exams_pp.examinations) > 0
        _exams_pp_ledger = exams_pp.create_ledger(name="SmartieExamsPP")
        interface_pp = PatientInterface(
            knowledge_base=lx_knowledge_base,
            patient_ledger=_exams_pp_ledger,
        )
        exams_pp.export_exam_findings_to_interface(interface_pp)

        # # test export for debugging ####
        # import yaml

        # ledger = interface_itt.patient_ledger
        # ledger_dump = ledger.to_ddict()

        # tmp_out_file = "./data/smartie/test_output_ledger_itt.yaml"

        # with open(tmp_out_file, "w", encoding="utf-8") as f:
        #     yaml.dump(ledger_dump, f)
