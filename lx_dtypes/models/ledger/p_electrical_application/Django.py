"""Django storage for electrical applications and regression comparisons."""

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)
from lx_dtypes.models.contracts.electrical_curve import (
    ELECTRICAL_CURVE_REGRESSION_ALGORITHM,
)

from .DataDict import PElectricalApplicationDataDict, PElectricalCurveComparisonDataDict


class PElectricalApplicationDjango(
    LedgerBaseModelDjango[PElectricalApplicationDataDict]
):
    patient_examination = models.CharField(max_length=255)
    electrical_curve_profile = models.CharField(max_length=255)
    knowledge_base_module = models.CharField(max_length=255)
    knowledge_base_version = models.CharField(max_length=255)
    measurement_source_sha256 = models.CharField(max_length=64)
    session_id = models.CharField(max_length=32)
    clock_id = models.CharField(max_length=32)
    time_base_num = models.BigIntegerField()
    time_base_den = models.BigIntegerField()
    sample_start_index = models.BigIntegerField()
    sample_end_index = models.BigIntegerField()
    start_timestamp = models.BigIntegerField()
    end_timestamp = models.BigIntegerField()
    started_at = models.DateTimeField()
    curve = models.JSONField()

    @property
    def ddict_class(self) -> type[PElectricalApplicationDataDict]:
        return PElectricalApplicationDataDict

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False


class PElectricalCurveComparisonDjango(
    LedgerBaseModelDjango[PElectricalCurveComparisonDataDict]
):
    patient_examination = models.CharField(max_length=255)
    electrical_curve_profile = models.CharField(max_length=255)
    knowledge_base_module = models.CharField(max_length=255)
    knowledge_base_version = models.CharField(max_length=255)
    algorithm = models.CharField(
        max_length=64, default=ELECTRICAL_CURVE_REGRESSION_ALGORITHM
    )
    application = models.CharField(max_length=255)
    reference_applications = models.JSONField(default=list)
    result = models.JSONField()

    @property
    def ddict_class(self) -> type[PElectricalCurveComparisonDataDict]:
        return PElectricalCurveComparisonDataDict

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
