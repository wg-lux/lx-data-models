from typing import Dict

from pydantic import Field

from lx_dtypes.models.base_models.person import Person
from lx_dtypes.utils.factories.field_defaults import str_unknown_factory


class Patient(Person):
    center: str = Field(default_factory=str_unknown_factory)
    external_ids: Dict[str, str] = Field(default_factory=dict)

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
