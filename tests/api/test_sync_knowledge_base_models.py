import pytest

from lx_dtypes.contrib.lx_django.models import (
    ClassificationChoice as DjangoClassificationChoiceModel,
)
from lx_dtypes.contrib.lx_django.models import (
    ClassificationChoiceDescriptor as DjangoClassificationChoiceDescriptorModel,
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
from lx_dtypes.contrib.lx_django.models.core.information_source import (
    InformationSource as DjangoInformationSourceModel,
)
from lx_dtypes.contrib.lx_django.models.core.intervention import (
    Intervention as DjangoInterventionModel,
)
from lx_dtypes.contrib.lx_django.models.core.unit import (
    Unit as DjangoUnitModel,
)
from lx_dtypes.contrib.lx_django.models.core.unit import (
    UnitType as DjangoUnitTypeModel,
)
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
from lx_dtypes.models.core.information_source import InformationSource
from lx_dtypes.models.core.information_source_shallow import InformationSourceShallow
from lx_dtypes.models.core.intervention import Intervention
from lx_dtypes.models.core.intervention_shallow import InterventionShallow
from lx_dtypes.models.core.unit import Unit, UnitType
from lx_dtypes.models.core.unit_shallow import UnitShallow, UnitTypeShallow


# TODO add transform utils based on those tests
@pytest.mark.django_db
class TestKnowledgebaseBaseModelSync:
    def test_classification_choice_descriptor_sync(
        self,
        sample_classification_choice_descriptor_numeric: ClassificationChoiceDescriptor,
        sample_django_classification_choice_descriptor_numeric: DjangoClassificationChoiceDescriptorModel,
    ) -> None:
        assert (
            str(sample_django_classification_choice_descriptor_numeric.uuid)
            == sample_classification_choice_descriptor_numeric.uuid
        )
        ccd_dict = (
            sample_django_classification_choice_descriptor_numeric.to_ddict_shallow()
        )
        # Convert the Django model instance back to a Pydantic model
        converted_ccd = ClassificationChoiceDescriptorShallow.model_validate(ccd_dict)
        assert (
            converted_ccd.to_ddict_shallow()
            == sample_classification_choice_descriptor_numeric.to_ddict_shallow()
        )

    def test_classification_choice_sync(
        self,
        sample_classification_choice: ClassificationChoice,
        sample_django_classification_choice: DjangoClassificationChoiceModel,
    ) -> None:
        django_ddict = sample_django_classification_choice.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_cc = ClassificationChoiceShallow.model_validate(django_ddict)
        assert (
            converted_cc.to_ddict_shallow()
            == sample_classification_choice.to_ddict_shallow()
        )

    def test_classification_sync(
        self,
        sample_classification: Classification,
        sample_django_classification: DjangoClassificationModel,
    ) -> None:
        classification_dict = sample_django_classification.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_classification = ClassificationShallow.model_validate(
            classification_dict
        )
        assert (
            converted_classification.to_ddict_shallow()
            == sample_classification.to_ddict_shallow()
        )

    def test_unit_sync(
        self,
        sample_unit: Unit,
        sample_unit_type: UnitType,
        sample_django_unit_type: DjangoUnitTypeModel,
        sample_django_unit: DjangoUnitModel,
    ) -> None:
        unit_type_dict = sample_django_unit_type.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_unit_type = UnitTypeShallow.model_validate(unit_type_dict)
        assert (
            converted_unit_type.to_ddict_shallow()
            == sample_unit_type.to_ddict_shallow()
        )

        unit_dict = sample_django_unit.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_unit = UnitShallow.model_validate(unit_dict)
        assert converted_unit.to_ddict_shallow() == sample_unit.to_ddict_shallow()

    def test_intervention_sync(
        self,
        sample_intervention: Intervention,
        sample_django_intervention: DjangoInterventionModel,
    ) -> None:
        intervention_dict = sample_django_intervention.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_intervention = InterventionShallow.model_validate(intervention_dict)
        assert (
            converted_intervention.to_ddict_shallow()
            == sample_intervention.to_ddict_shallow()
        )

    def test_finding_sync(
        self, sample_finding: Finding, sample_django_finding: DjangoFindingModel
    ) -> None:
        finding_dict = sample_django_finding.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_finding = FindingShallow.model_validate(finding_dict)
        assert converted_finding.to_ddict_shallow() == sample_finding.to_ddict_shallow()

    def test_indication_sync(
        self,
        sample_indication: Indication,
        sample_django_indication: DjangoIndicationModel,
    ) -> None:
        indication_dict = sample_django_indication.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_indication = IndicationShallow.model_validate(indication_dict)
        assert (
            converted_indication.to_ddict_shallow()
            == sample_indication.to_ddict_shallow()
        )

    def test_examination_sync(
        self,
        sample_examination: Examination,
        sample_django_examination: DjangoExaminationModel,
    ) -> None:
        examination_dict = sample_django_examination.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_examination = ExaminationShallow.model_validate(examination_dict)
        assert (
            converted_examination.to_ddict_shallow()
            == sample_examination.to_ddict_shallow()
        )

    def test_citation_sync(
        self, sample_citation: Citation, sample_django_citation: DjangoCitationModel
    ) -> None:
        citation_dict = sample_django_citation.to_ddict_shallow()
        converted_citation = CitationShallow.model_validate(citation_dict)
        assert (
            converted_citation.to_ddict_shallow() == sample_citation.to_ddict_shallow()
        )

    def test_information_source_sync(
        self,
        sample_information_source: InformationSource,
        sample_django_information_source: DjangoInformationSourceModel,
    ) -> None:
        information_source_dict = sample_django_information_source.to_ddict_shallow()
        # Convert the Django model instance back to a Pydantic model
        converted_information_source = InformationSourceShallow.model_validate(
            information_source_dict
        )
        assert (
            converted_information_source.to_ddict_shallow()
            == sample_information_source.to_ddict_shallow()
        )

    # def test_patient_examination_sync(self, sample_patient_examination: PatientExamination) -> None:

    #
