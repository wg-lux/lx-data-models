"""Django storage for time-offset observations; semantic checks use Pydantic."""

from django.db import models

from lx_dtypes.models.base.app_base_model.django.LedgerBaseModelDjango import (
    LedgerBaseModelDjango,
)

from .DataDict import PTimeOffsetDataDict


class PTimeOffsetDjango(LedgerBaseModelDjango[PTimeOffsetDataDict]):
    patient_examination = models.CharField(max_length=255)
    time_reference = models.CharField(max_length=255)
    knowledge_base_module = models.CharField(max_length=255)
    knowledge_base_version = models.CharField(max_length=255)
    evidence = models.JSONField()

    @property
    def ddict_class(self) -> type[PTimeOffsetDataDict]:
        return PTimeOffsetDataDict

    class Meta(LedgerBaseModelDjango.Meta):
        abstract = False
