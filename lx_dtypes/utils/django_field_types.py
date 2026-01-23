import datetime
import uuid as uuid_module
from typing import TYPE_CHECKING, Any, Dict, TypeAlias

from django.db import models

if TYPE_CHECKING:
    UUIDFieldType: TypeAlias = models.UUIDField[uuid_module.UUID, uuid_module.UUID]
    OptionalCharFieldType: TypeAlias = models.CharField[str | None, str | None]
    CharFieldType: TypeAlias = models.CharField[str, str]
    OptionalEmailFieldType: TypeAlias = models.EmailField[str | None, str | None]
    OptionalDateFieldType: TypeAlias = models.DateField[
        datetime.date | None, datetime.date | None
    ]
    JSONFieldType: TypeAlias = models.JSONField[Dict[str, Any], Dict[str, Any]]
    OptionalJSONFieldType: TypeAlias = models.JSONField[
        Dict[str, Any] | None, Dict[str, Any] | None
    ]
    DateTimeField: TypeAlias = models.DateTimeField[
        datetime.datetime, datetime.datetime
    ]
    OptionalDateTimeField: TypeAlias = models.DateTimeField[
        datetime.datetime | None, datetime.datetime | None
    ]
    FloatFieldType: TypeAlias = models.FloatField[float, float]
    OptionalFloatFieldType: TypeAlias = models.FloatField[float | None, float | None]
    IntegerFieldType: TypeAlias = models.IntegerField[int, int]
    OptionalIntegerFieldType: TypeAlias = models.IntegerField[int | None, int | None]
    BooleanFieldType: TypeAlias = models.BooleanField[bool, bool]
else:  # Runtime fallbacks keep Django field classes unsubscripted
    UUIDFieldType: TypeAlias = models.UUIDField
    OptionalCharFieldType: TypeAlias = models.CharField
    CharFieldType: TypeAlias = models.CharField
    OptionalEmailFieldType: TypeAlias = models.EmailField
    OptionalDateFieldType: TypeAlias = models.DateField
    JSONFieldType: TypeAlias = models.JSONField
    OptionalJSONFieldType: TypeAlias = models.JSONField
    DateTimeField: TypeAlias = models.DateTimeField
    OptionalDateTimeField: TypeAlias = models.DateTimeField
    FloatFieldType: TypeAlias = models.FloatField
    OptionalFloatFieldType: TypeAlias = models.FloatField
    IntegerFieldType: TypeAlias = models.IntegerField
    OptionalIntegerFieldType: TypeAlias = models.IntegerField
    BooleanFieldType: TypeAlias = models.BooleanField
