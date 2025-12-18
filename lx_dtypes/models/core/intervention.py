from typing import Dict

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import intervention_type_by_name_factory

from .intervention_shallow import (
    InterventionShallow,
    InterventionShallowDataDict,
    InterventionTypeShallow,
    InterventionTypeShallowDataDict,
)


class InterventionTypeDataDict(InterventionTypeShallowDataDict):
    pass


class InterventionDataDict(InterventionShallowDataDict):
    types: Dict[str, InterventionTypeDataDict]


class InterventionType(InterventionTypeShallow):
    """Taggable shell for intervention type metadata."""

    @property
    def ddict_shallow(self) -> type[InterventionTypeShallowDataDict]:
        return InterventionTypeShallowDataDict

    def to_ddict_shallow(self) -> InterventionTypeShallowDataDict:
        dump = self.model_dump()
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }
        return self.ddict_shallow(**shallow_data)


class Intervention(InterventionShallow):
    """
    Shallow Model to represent a medical intervention.
    Attributes:
        name (str): The name of the classification choice.
        name_de (str | None): The German name of the classification choice.
        name_en (str | None): The English name of the classification choice.
        description (str | None): The description of the classification choice.
        expected_intervention_names (list[str]): Names of expected interventions.
        causes_finding_names (list[str]): Names of findings caused by this intervention.
        type_names (list[str]): Names of associated intervention types.
    """

    types: Dict[str, InterventionType] = Field(
        default_factory=intervention_type_by_name_factory
    )

    def _sync_shallow_fields(self) -> None:
        """Sync shallow fields from related models."""
        # TODO maybe protect if already set?
        if self.types:
            self.type_names = [
                intervention_type.name for intervention_type in self.types.values()
            ]
        else:
            self.type_names = []

    @property
    def ddict(self) -> type[InterventionDataDict]:
        return InterventionDataDict

    def to_ddict_shallow(self) -> InterventionShallowDataDict:
        self._sync_shallow_fields()
        dump = self.model_dump()
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }
        return self.ddict_shallow(**shallow_data)
