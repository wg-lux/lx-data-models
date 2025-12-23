from typing import List, Literal

LEDGER_MODEL_NAMES_LITERAL = Literal[
    "center",
    "examiner",
    "patient",
    "patient_examination",
    "patient_indication",
    "patient_finding",
    "patient_finding_classifications",
    "patient_finding_classification_choice",
    "patient_finding_classification_choice_descriptor",
    # patient_intervention", #TODO: implement patient intervention model
]

LEDGER_MODEL_NAMES_ORDERED: List[LEDGER_MODEL_NAMES_LITERAL] = [
    "center",
    "examiner",
    "patient",
    "patient_examination",
    "patient_indication",
    "patient_finding",
    "patient_finding_classifications",
    "patient_finding_classification_choice",
    "patient_finding_classification_choice_descriptor",
    # patient_intervention", #TODO: implement patient intervention model
]

KB_MODEL_NAMES_LITERAL = Literal[
    "citation",
    "classification",
    "classification_type",
    "classification_choice",
    "classification_choice_descriptor",
    "examination",
    "examination_type",
    "finding",
    "finding_type",
    "indication",
    "indication_type",
    "intervention",
    "intervention_type",
    "unit",
    "unit_type",
    "information_source",
]

KB_MODEL_NAMES_ORDERED: List[KB_MODEL_NAMES_LITERAL] = [
    "information_source",
    "citation",
    "unit_type",
    "unit",
    "classification_choice_descriptor",
    "classification_choice",
    "classification_type",
    "classification",
    "finding_type",
    "finding",
    "intervention_type",
    "intervention",
    "indication_type",
    "indication",
    "examination_type",
    "examination",
]

# from lx_dtypes.lx_django.models.core.citation import (
#     Citation as CitationDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.classification import (
#     Classification as ClassificationDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.classification import (
#     ClassificationType as ClassificationTypeDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.classification_choice import (
#     ClassificationChoice as ClassificationChoiceDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.classification_choice_descriptor import (
#     ClassificationChoiceDescriptor as ClassificationChoiceDescriptorDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.examination import (
#     Examination as ExaminationDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.examination import (
#     ExaminationType as ExaminationTypeDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.finding import (
#     Finding as FindingDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.finding import (
#     FindingType as FindingTypeDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.indication import (
#     Indication as IndicationDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.indication import (
#     IndicationType as IndicationTypeDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.intervention import (
#     Intervention as InterventionDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.intervention import (
#     InterventionType as InterventionTypeDjangoModel,
# )
# from lx_dtypes.lx_django.models.core.unit import Unit as UnitDjangoModel
# from lx_dtypes.lx_django.models.core.unit import UnitType as UnitTypeDjangoModel
# from lx_dtypes.models.core.citation_shallow import (
#     CitationShallow,
#     CitationShallowDataDict,
# )
# from lx_dtypes.models.core.classification_choice_descriptor_shallow import (
#     ClassificationChoiceDescriptorShallow,
#     ClassificationChoiceDescriptorShallowDataDict,
# )
# from lx_dtypes.models.core.classification_choice_shallow import (
#     ClassificationChoiceShallow,
#     ClassificationChoiceShallowDataDict,
# )
# from lx_dtypes.models.core.classification_shallow import (
#     ClassificationShallow,
#     ClassificationShallowDataDict,
#     ClassificationTypeShallow,
#     ClassificationTypeShallowDataDict,
# )
# from lx_dtypes.models.core.examination_shallow import (
#     ExaminationShallow,
#     ExaminationShallowDataDict,
#     ExaminationTypeShallow,
#     ExaminationTypeShallowDataDict,
# )
# from lx_dtypes.models.core.finding_shallow import (
#     FindingShallow,
#     FindingShallowDataDict,
#     FindingTypeShallow,
#     FindingTypeShallowDataDict,
# )
# from lx_dtypes.models.core.indication_shallow import (
#     IndicationShallow,
#     IndicationShallowDataDict,
#     IndicationTypeShallow,
#     IndicationTypeShallowDataDict,
# )
# from lx_dtypes.models.core.intervention_shallow import (
#     InterventionShallow,
#     InterventionShallowDataDict,
#     InterventionTypeShallow,
#     InterventionTypeShallowDataDict,
# )
# from lx_dtypes.models.core.unit_shallow import (
#     UnitShallow,
#     UnitShallowDataDict,
#     UnitTypeShallow,
#     UnitTypeShallowDataDict,
# )

# from .ddict.knowledge_base_shallow import (
#     KB_SHALLOW_DDICT_BY_NAME,
#     KB_SHALLOW_DDICT_BY_NAME_TYPE,
# )
# from .django.kb_models import KB_DJANGO_MODEL_BY_NAME, KB_DJANGO_MODEL_BY_NAME_TYPE
# from .pydantic.knowledge_base_shallow import (
#     KB_SHALLOW_PYDANTIC_BY_NAME,
#     KB_SHALLOW_PYDANTIC_BY_NAME_TYPE,
# )


# class KB_MODELS:
#     django: KB_DJANGO_MODEL_BY_NAME_TYPE
#     pydantic: KB_SHALLOW_PYDANTIC_BY_NAME_TYPE
#     ddict: KB_SHALLOW_DDICT_BY_NAME_TYPE

#     def get_models_by_name(
#         self,
#         model_name: KB_MODEL_NAMES,
#     ):
#         django_model = self.django[model_name]
#         pydantic_model = self.pydantic[model_name]
#         ddict_model = self.ddict[model_name]
#         return django_model, pydantic_model, ddict_model


# def get_kbmodels_by_name(
#     model_name: KB_MODEL_NAMES,
# ):
#     ddict_type = KB_SHALLOW_DDICT_BY_NAME[model_name]
#     pydantic_type = KB_SHALLOW_PYDANTIC_BY_NAME[model_name]
#     django_model = KB_DJANGO_MODEL_BY_NAME[model_name]
#     return ddict_type, pydantic_type, django_model
