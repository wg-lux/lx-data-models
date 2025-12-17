from typing import Dict, NotRequired, Optional, TypedDict

from pydantic import Field

from lx_dtypes.models.base_models.person import Person
from lx_dtypes.utils.factories.field_defaults import str_unknown_factory


class PatientDataDict(TypedDict):
    uuid: NotRequired[str]
    first_name: str
    last_name: str
    dob: Optional[str]
    center_name: str
    gender: str
    external_ids: NotRequired[Optional[Dict[str, str]]]


class PatientDataShallowDict(TypedDict):
    uuid: NotRequired[str]
    first_name: str
    last_name: str
    dob: Optional[str]
    center_name: str
    gender: str


class PatientShallow(Person):
    center_name: str = Field(default_factory=str_unknown_factory)

    @property
    def ddict_shallow(self) -> type[PatientDataShallowDict]:
        return PatientDataShallowDict

    def to_ddict_shallow(self) -> PatientDataShallowDict:
        """Convert the PatientShallow instance to a PatientDataShallowDict.

        Returns:
            PatientDataShallowDict: The converted shallow data dictionary.
        """
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class Patient(PatientShallow):
    external_ids: Dict[str, str] = Field(default_factory=dict)

    @property
    def ddict(self) -> type[PatientDataDict]:
        return PatientDataDict

    @classmethod
    def create_from_person(cls, person: Person) -> "Patient":
        """Create a Patient instance from a Person instance.

        Args:
            person (Person): The Person instance to convert.
        Returns:
            Patient: The created Patient instance.
        """
        patient_dict = person.model_dump()
        return cls(**patient_dict)

    def to_ddict(self) -> PatientDataDict:
        """Convert the Patient instance to a PatientDataDict.

        Returns:
            PatientDataDict: The converted data dictionary.
        """
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(self) -> PatientDataShallowDict:
        """Convert the Patient instance to a PatientDataShallowDict.

        Returns:
            PatientDataShallowDict: The converted shallow data dictionary.
        """

        dump = self.model_dump()
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }

        return self.ddict_shallow(**shallow_data)
