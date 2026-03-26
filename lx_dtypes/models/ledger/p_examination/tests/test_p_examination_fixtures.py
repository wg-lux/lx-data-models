from pathlib import Path

import pytest

from lx_dtypes.models.ledger.p_finding.Django import PFindingDjango
from lx_dtypes.models.ledger.p_indication.Django import PIndicationDjango
from lx_dtypes.utils.testing import validate_django_fixture

from ..Django import PExaminationDjango
from ..Pydantic import PExamination


@pytest.mark.django_db
class TestPExaminationFixtures:
    def test_p_examination_fixture(self, p_examination_fixture: PExamination) -> None:
        assert p_examination_fixture is not None
        ddict = p_examination_fixture.ddict
        new_obj = p_examination_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert p_examination_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        p_examination_fixture.to_yaml(
            Path(__file__).parent / "p_examination_fixture.yaml"
        )

    def test_p_examination_fixture_preserves_knowledge_base_identity(self) -> None:
        fixture = PExamination(
            patient="patient-1",
            examination="sample_examination",
            knowledge_base_module="report_template_examples",
            knowledge_base_version="0.1.0",
        )

        ddict = fixture.ddict

        assert ddict["knowledge_base_module"] == "report_template_examples"
        assert ddict["knowledge_base_version"] == "0.1.0"


@pytest.mark.django_db
class TestDjangoPExaminationFixture:
    def test_django_p_examination_fixture(
        self,
        django_p_examination_fixture: PExaminationDjango,
    ) -> None:
        assert django_p_examination_fixture is not None
        assert django_p_examination_fixture.knowledge_base_module == "report_template_examples"
        assert django_p_examination_fixture.knowledge_base_version == "0.1.0"
        assert django_p_examination_fixture.ddict["knowledge_base_module"] == "report_template_examples"
        assert django_p_examination_fixture.ddict["knowledge_base_version"] == "0.1.0"

        validate_django_fixture(django_p_examination_fixture)

    def test_populated_django_p_examination_fixture(
        self,
        django_populated_p_examination_fixture: PExaminationDjango,
        django_populated_p_finding_fixture: PFindingDjango,
        django_p_indication_fixture: PIndicationDjango,
    ) -> None:
        """
        Validate a populated Django-backed PExamination fixture, export its Pydantic representation to YAML, and run Django fixture validation.

        Parameters:
            django_populated_p_examination_fixture (PExaminationDjango): A Django fixture for a populated PExamination.
            django_populated_p_finding_fixture (PFindingDjango): A related populated PFinding Django fixture used to ensure cross-fixture relationships exist.
            django_p_indication_fixture (PIndicationDjango): A related PIndication Django fixture used to ensure cross-fixture relationships exist.
        """
        assert django_populated_p_examination_fixture is not None

        _ddict = django_populated_p_examination_fixture.ddict
        assert _ddict["knowledge_base_module"] == "report_template_examples"
        assert _ddict["knowledge_base_version"] == "0.1.0"
        for key, value in _ddict.items():
            print(f"{key}: {value}")
        pydantic_instance = PExamination.model_validate(_ddict)

        pydantic_instance.to_yaml(
            Path(__file__).parent / "populated_p_examination_fixture.yaml"
        )
        validate_django_fixture(django_populated_p_examination_fixture)

    def test_django_p_examination_syncs_knowledge_base_identity(
        self,
        p_examination_fixture: PExamination,
    ) -> None:
        instance = PExaminationDjango.sync_from_ddict(
            p_examination_fixture.model_copy(
                update={
                    "knowledge_base_module": "report_template_examples",
                    "knowledge_base_version": "0.1.0",
                }
            ).ddict
        )

        assert instance.knowledge_base_module == "report_template_examples"
        assert instance.knowledge_base_version == "0.1.0"
        assert instance.ddict["knowledge_base_module"] == "report_template_examples"
        assert instance.ddict["knowledge_base_version"] == "0.1.0"
