from typing import TYPE_CHECKING, Any, Dict

from pydantic import Field, field_serializer

from lx_dtypes.models.shallow.center import CenterShallow
from lx_dtypes.utils.factories.field_defaults import (
    examiner_by_uuid_factory,
)

if TYPE_CHECKING:
    from lx_dtypes.models.examiner.examiner import Examiner


class Center(CenterShallow):
    """Model representing a Center."""

    examiners: Dict[str, "Examiner"] = Field(default_factory=examiner_by_uuid_factory)

    @field_serializer("examiners")
    def serialize_examiners(self, examiners: Dict[str, "Examiner"]) -> Dict[str, Any]:
        r: Dict[str, Any] = {
            examiner_uuid: examiner.model_dump()
            for examiner_uuid, examiner in examiners.items()
        }
        return r
