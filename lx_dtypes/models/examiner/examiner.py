from datetime import date
from typing import Dict, NotRequired, Optional, TypedDict

from pydantic import Field

from lx_dtypes.models.base_models.person import Person
from lx_dtypes.utils.factories.field_defaults import str_unknown_factory


class ExaminerDataDict(TypedDict):
    first_name: Optional[str]
    last_name: str
    dob: date
    center: str
    gender: NotRequired[Optional[str]]
    external_ids: Optional[Dict[str, str]]
    uuid: NotRequired[str]


class Examiner(Person):
    center_name: str = Field(default_factory=str_unknown_factory)
    external_ids: Dict[str, str] = Field(default_factory=dict)

    @classmethod
    def create_from_person(cls, person: Person) -> "Examiner":
        """Create an Examiner instance from a Person instance.

        Args:
            person (Person): The Person instance to convert.
        Returns:
            Examiner: The created Examiner instance.
        """
        examiner_dict = person.model_dump()

        return cls.model_validate(examiner_dict)
