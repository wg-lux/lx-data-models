from typing import Any, Dict

from pydantic import Field, field_serializer

from lx_dtypes.models.core.center_shallow import CenterShallow, CenterShallowDataDict
from lx_dtypes.models.ledger.examiner import Examiner, ExaminerDataDict
from lx_dtypes.utils.factories.field_defaults import (
    examiner_by_uuid_factory,
)


# TODO Move Outside Core since this is not a kb model
class CenterDataDict(CenterShallowDataDict):
    examiners: Dict[str, ExaminerDataDict]


class Center(CenterShallow):
    """Model representing a Center."""

    examiners: Dict[str, Examiner] = Field(default_factory=examiner_by_uuid_factory)

    @property
    def ddict(self) -> type[CenterDataDict]:
        return CenterDataDict

    @field_serializer("examiners")
    def serialize_examiners(self, examiners: Dict[str, "Examiner"]) -> Dict[str, Any]:
        r: Dict[str, ExaminerDataDict] = {
            examiner_uuid: examiner.to_ddict()
            for examiner_uuid, examiner in examiners.items()
        }
        return r

    def to_ddict(self) -> CenterDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(self) -> CenterShallowDataDict:
        # TODO add this design pattern to documentation for easy re-use
        examiner_uuids = list(self.examiners.keys())
        dump = self.model_dump()
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }

        shallow_data["examiner_uuids"] = examiner_uuids

        return self.ddict_shallow(**shallow_data)
