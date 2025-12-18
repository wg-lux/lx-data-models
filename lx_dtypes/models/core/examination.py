from typing import Dict

from pydantic import Field, field_serializer

from lx_dtypes.models.core.examination_shallow import (
    ExaminationShallow,
    ExaminationShallowDataDict,
    ExaminationTypeShallow,
    ExaminationTypeShallowDataDict,
)

from .finding import Finding, FindingDataDict
from .indication import Indication, IndicationDataDict


class ExaminationTypeDataDict(ExaminationTypeShallowDataDict):
    pass


class ExaminationDataDict(ExaminationShallowDataDict):
    findings: Dict[str, FindingDataDict]
    types: Dict[str, ExaminationTypeDataDict]
    indications: Dict[str, IndicationDataDict]


class ExaminationType(ExaminationTypeShallow):
    """Model representing an examination type."""

    pass

    @property
    def ddict(self) -> type[ExaminationTypeDataDict]:
        return ExaminationTypeDataDict

    def to_ddict(self) -> ExaminationTypeDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict


class Examination(ExaminationShallow):
    """Model representing a finding classification."""

    findings: Dict[str, "Finding"] = Field(default_factory=dict)
    types: Dict[str, ExaminationType] = Field(default_factory=dict)
    indications: Dict[str, "Indication"] = Field(default_factory=dict)

    @field_serializer("findings")
    def serialize_findings(
        self, findings: Dict[str, "Finding"]
    ) -> Dict[str, FindingDataDict]:
        return {
            finding_uuid: finding.to_ddict()
            for finding_uuid, finding in findings.items()
        }

    @field_serializer("indications")
    def serialize_indications(
        self, indications: Dict[str, "Indication"]
    ) -> Dict[str, IndicationDataDict]:
        return {
            indication_uuid: indication.to_ddict()
            for indication_uuid, indication in indications.items()
        }

    @field_serializer("types")
    def serialize_types(
        self, types: Dict[str, ExaminationType]
    ) -> Dict[str, ExaminationTypeDataDict]:
        return {type_uuid: type_.to_ddict() for type_uuid, type_ in types.items()}

    @property
    def ddict(self) -> type[ExaminationDataDict]:
        return ExaminationDataDict

    def _sync_shallow_fields(self) -> None:
        """Sync shallow fields from deep fields."""
        if self.findings:
            self.finding_names = list(self.findings.keys())

        if self.types:
            self.type_names = list(self.types.keys())

        if self.indications:
            self.indication_names = list(self.indications.keys())

    def to_ddict(self) -> ExaminationDataDict:
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(self) -> ExaminationShallowDataDict:
        self._sync_shallow_fields()
        dump = self.model_dump()
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }

        return self.ddict_shallow(**shallow_data)
