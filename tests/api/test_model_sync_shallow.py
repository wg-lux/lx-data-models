import pytest

from lx_dtypes.contrib.lx_django.models import (
    Center as DjangoCenterModel,
)
from lx_dtypes.contrib.lx_django.models import (
    ClassificationChoice as DjangoClassificationChoiceModel,
)
from lx_dtypes.contrib.lx_django.models import (
    ClassificationChoiceDescriptor as DjangoClassificationChoiceDescriptorModel,
)
from lx_dtypes.contrib.lx_django.models import (
    Examiner as DjangoExaminerModel,
)
from lx_dtypes.contrib.lx_django.models import (
    Patient as DjangoPatientModel,
)
from lx_dtypes.contrib.lx_django.models.core.citation import (
    Citation as DjangoCitationModel,
)
from lx_dtypes.contrib.lx_django.models.core.classification import (
    Classification as DjangoClassificationModel,
)
from lx_dtypes.contrib.lx_django.models.core.examination import (
    Examination as DjangoExaminationModel,
)
from lx_dtypes.contrib.lx_django.models.core.finding import (
    Finding as DjangoFindingModel,
)
from lx_dtypes.contrib.lx_django.models.core.indication import (
    Indication as DjangoIndicationModel,
)
from lx_dtypes.contrib.lx_django.models.core.intervention import (
    Intervention as DjangoInterventionModel,
)
from lx_dtypes.contrib.lx_django.models.core.unit import (
    Unit as DjangoUnitModel,
)
from lx_dtypes.models.core.center import Center
from lx_dtypes.models.core.center_shallow import CenterShallow
from lx_dtypes.models.core.citation import Citation
from lx_dtypes.models.core.citation_shallow import CitationShallow
from lx_dtypes.models.core.classification import Classification
from lx_dtypes.models.core.classification_choice import ClassificationChoice
from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.core.classification_choice_descriptor_shallow import (
    ClassificationChoiceDescriptorShallow,
)
from lx_dtypes.models.core.classification_choice_shallow import (
    ClassificationChoiceShallow,
)
from lx_dtypes.models.core.classification_shallow import ClassificationShallow
from lx_dtypes.models.core.examination import Examination
from lx_dtypes.models.core.examination_shallow import ExaminationShallow
from lx_dtypes.models.core.finding import Finding
from lx_dtypes.models.core.finding_shallow import FindingShallow
from lx_dtypes.models.core.indication import Indication
from lx_dtypes.models.core.indication_shallow import IndicationShallow
from lx_dtypes.models.core.intervention import Intervention
from lx_dtypes.models.core.intervention_shallow import InterventionShallow
from lx_dtypes.models.core.unit import Unit
from lx_dtypes.models.core.unit_shallow import UnitShallow
from lx_dtypes.models.examiner.examiner import Examiner, ExaminerShallow
from lx_dtypes.models.patient.patient import Patient, PatientShallow


# TODO add transform utils based on those tests
@pytest.mark.django_db
class TestModelSync:
    # TODO Move to ledger test file when created
    def test_patient_sync(self, sample_patient: Patient) -> None:
        ddict = sample_patient.to_ddict_shallow()
        _django_patient = DjangoPatientModel.objects.create(**ddict)
        uuid = ddict.get("uuid")
        assert uuid is not None
        retrieved_patient = DjangoPatientModel.objects.get(uuid=uuid)
        assert str(retrieved_patient.uuid) == sample_patient.uuid
        patient_dict = retrieved_patient.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_patient = PatientShallow.model_validate(patient_dict)
        assert converted_patient.to_ddict_shallow() == sample_patient.to_ddict_shallow()

    # TODO Move to ledger test file when created
    def test_examiner_sync(self, sample_examiner: Examiner) -> None:
        ddict = sample_examiner.to_ddict_shallow()
        _django_examiner = DjangoExaminerModel.objects.create(**ddict)
        uuid = ddict.get("uuid")
        assert uuid is not None
        retrieved_examiner = DjangoExaminerModel.objects.get(uuid=uuid)
        assert str(retrieved_examiner.uuid) == sample_examiner.uuid
        examiner_dict = retrieved_examiner.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_examiner = ExaminerShallow.model_validate(examiner_dict)
        assert (
            converted_examiner.to_ddict_shallow() == sample_examiner.to_ddict_shallow()
        )

    def test_center_sync(self, sample_center: Center) -> None:
        ddict = sample_center.to_ddict_shallow()
        _django_center = DjangoCenterModel.objects.create(**ddict)
        uuid = ddict.get("uuid")
        assert uuid is not None
        retrieved_center = DjangoCenterModel.objects.get(uuid=uuid)
        assert str(retrieved_center.uuid) == sample_center.uuid
        center_dict = retrieved_center.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_center = CenterShallow.model_validate(center_dict)
        assert converted_center.to_ddict_shallow() == sample_center.to_ddict_shallow()

    def test_classification_choice_descriptor_sync(
        self,
        sample_classification_choice_descriptor_numeric: ClassificationChoiceDescriptor,
    ) -> None:
        ddict = sample_classification_choice_descriptor_numeric.to_ddict_shallow()
        _django_ccd = DjangoClassificationChoiceDescriptorModel.objects.create(**ddict)
        uuid = ddict.get("uuid")
        assert uuid is not None
        retrieved_ccd = DjangoClassificationChoiceDescriptorModel.objects.get(uuid=uuid)
        assert (
            str(retrieved_ccd.uuid)
            == sample_classification_choice_descriptor_numeric.uuid
        )
        ccd_dict = retrieved_ccd.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_ccd = ClassificationChoiceDescriptorShallow.model_validate(ccd_dict)
        assert (
            converted_ccd.to_ddict_shallow()
            == sample_classification_choice_descriptor_numeric.to_ddict_shallow()
        )

    def test_classification_choice_sync(
        self, sample_classification_choice: ClassificationChoice
    ) -> None:
        ddict = sample_classification_choice.to_ddict_shallow()
        django_cc = DjangoClassificationChoiceModel.objects.create(**ddict)
        django_cc.refresh_from_db()
        cc_dict = django_cc.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_cc = ClassificationChoiceShallow.model_validate(cc_dict)
        assert (
            converted_cc.to_ddict_shallow()
            == sample_classification_choice.to_ddict_shallow()
        )

    def test_classification_sync(self, sample_classification: Classification) -> None:
        ddict = sample_classification.to_ddict_shallow()
        django_classification = DjangoClassificationModel.objects.create(**ddict)
        django_classification.refresh_from_db()
        classification_dict = django_classification.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_classification = ClassificationShallow.model_validate(
            classification_dict
        )
        assert (
            converted_classification.to_ddict_shallow()
            == sample_classification.to_ddict_shallow()
        )

    def test_unit_sync(self, sample_unit: Unit) -> None:
        ddict = sample_unit.to_ddict_shallow()
        django_unit = DjangoUnitModel.objects.create(**ddict)
        django_unit.refresh_from_db()
        unit_dict = django_unit.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_unit = UnitShallow.model_validate(unit_dict)
        assert converted_unit.to_ddict_shallow() == sample_unit.to_ddict_shallow()

    def test_intervention_sync(self, sample_intervention: Intervention) -> None:
        ddict = sample_intervention.to_ddict_shallow()
        django_intervention = DjangoInterventionModel.objects.create(**ddict)
        django_intervention.refresh_from_db()
        intervention_dict = django_intervention.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_intervention = InterventionShallow.model_validate(intervention_dict)
        assert (
            converted_intervention.to_ddict_shallow()
            == sample_intervention.to_ddict_shallow()
        )

    def test_finding_sync(self, sample_finding: Finding) -> None:
        ddict = sample_finding.to_ddict_shallow()
        django_finding = DjangoFindingModel.objects.create(**ddict)
        django_finding.refresh_from_db()
        finding_dict = django_finding.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_finding = FindingShallow.model_validate(finding_dict)
        assert converted_finding.to_ddict_shallow() == sample_finding.to_ddict_shallow()

    def test_indication_sync(self, sample_indication: Indication) -> None:
        ddict = sample_indication.to_ddict_shallow()
        django_indication = DjangoIndicationModel.objects.create(**ddict)
        django_indication.refresh_from_db()
        indication_dict = django_indication.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_indication = IndicationShallow.model_validate(indication_dict)
        assert (
            converted_indication.to_ddict_shallow()
            == sample_indication.to_ddict_shallow()
        )

    def test_examination_sync(self, sample_examination: Examination) -> None:
        ddict = sample_examination.to_ddict_shallow()
        django_examination = DjangoExaminationModel.objects.create(**ddict)
        django_examination.refresh_from_db()
        examination_dict = django_examination.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_examination = ExaminationShallow.model_validate(examination_dict)
        assert (
            converted_examination.to_ddict_shallow()
            == sample_examination.to_ddict_shallow()
        )

    def test_citation_sync(self, sample_citation: Citation) -> None:
        ddict = sample_citation.to_ddict_shallow()
        django_citation = DjangoCitationModel.objects.create(**ddict)
        django_citation.refresh_from_db()
        citation_dict = django_citation.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_citation = CitationShallow.model_validate(citation_dict)
        assert (
            converted_citation.to_ddict_shallow() == sample_citation.to_ddict_shallow()
        )

    # def test_information_source_sync(self, sample_information_source: InformationSource) -> None:

    # def test_patient_examination_sync(self, sample_patient_examination: PatientExamination) -> None:

    #
