from typing import Any, ClassVar

import pandera.pandas as pa

from lx_dtypes.models.knowledge_base.citation.Citation import Citation
from lx_dtypes.models.knowledge_base.classification.Classification import Classification
from lx_dtypes.models.knowledge_base.classification.ClassificationType import (
    ClassificationType,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.examination.Examination import Examination
from lx_dtypes.models.knowledge_base.examination.ExaminationType import ExaminationType
from lx_dtypes.models.knowledge_base.finding._Finding import Finding
from lx_dtypes.models.knowledge_base.finding._FindingType import FindingType
from lx_dtypes.models.knowledge_base.indication.Indication import Indication
from lx_dtypes.models.knowledge_base.indication.IndicationType import IndicationType
from lx_dtypes.models.knowledge_base.information_source.InformationSource import (
    InformationSource,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceType import (
    InformationSourceType,
)
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.intervention.InterventionType import (
    InterventionType,
)
from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitType import UnitType

from .common import COERCE, PANDERA_PYDANTIC_MODEL


class CitationDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Citation)


class ClassificationDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Classification)


class ClassificationTypeDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ClassificationType)


class ClassificationChoiceDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ClassificationChoice)


class ClassificationChoiceDescriptorDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ClassificationChoiceDescriptor)


class ExaminationDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Examination)


class ExaminationTypeDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ExaminationType)


class FindingDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Finding)


class FindingTypeDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(FindingType)


class IndicationDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Indication)


class IndicationTypeDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(IndicationType)


class InformationSourceDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(InformationSource)


class InformationSourceTypeDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(InformationSourceType)


class InterventionDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Intervention)


class InterventionTypeDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(InterventionType)


class UnitDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(Unit)


class UnitTypeDfSchema(pa.DataFrameModel):
    class Config:  # type: ignore
        coerce = COERCE
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(UnitType)
