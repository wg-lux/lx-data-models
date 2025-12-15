from typing import Any, ClassVar

import pandera.pandas as pa

from lx_dtypes.models.shallow import (
    CitationShallow,
    ClassificationChoiceDescriptorShallow,
    ClassificationChoiceShallow,
    ClassificationShallow,
    ClassificationTypeShallow,
    ExaminationShallow,
    ExaminationTypeShallow,
    FindingShallow,
    FindingTypeShallow,
    IndicationShallow,
    IndicationTypeShallow,
    InformationSourceShallow,
    InterventionShallow,
    InterventionTypeShallow,
    UnitShallow,
    UnitTypeShallow,
)

from .common import COERCE, PANDERA_PYDANTIC_MODEL

# DOCS: https://pandera.readthedocs.io/en/stable/pydantic_integration.html#pydantic-integration


class CitationShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(CitationShallow)
        coerce = COERCE


class ClassificationChoiceDescriptorShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(
            ClassificationChoiceDescriptorShallow
        )
        coerce = COERCE


class ClassificationChoiceShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ClassificationChoiceShallow)
        coerce = COERCE


class ClassificationShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ClassificationShallow)
        coerce = COERCE


class ClassificationTypeShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ClassificationTypeShallow)
        coerce = COERCE


class ExaminationShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ExaminationShallow)
        coerce = COERCE


class ExaminationTypeShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(ExaminationTypeShallow)
        coerce = COERCE


class FindingShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(FindingShallow)
        coerce = COERCE


class FindingTypeShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(FindingTypeShallow)
        coerce = COERCE


class IndicationShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(IndicationShallow)
        coerce = COERCE


class IndicationTypeShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(IndicationTypeShallow)
        coerce = COERCE


class InformationSourceShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(InformationSourceShallow)
        coerce = COERCE


class InterventionShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(InterventionShallow)
        coerce = COERCE


class InterventionTypeShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(InterventionTypeShallow)
        coerce = COERCE


class UnitShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(UnitShallow)
        coerce = COERCE


class UnitTypeShallowSchema(pa.DataFrameModel):
    class Config:  # type:ignore # (pa.DataFrameModel.Config):
        dtype: ClassVar[Any] = PANDERA_PYDANTIC_MODEL(UnitTypeShallow)
        coerce = COERCE
