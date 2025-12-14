from datetime import date
from typing import Dict, NotRequired, Optional, TypedDict

from pydantic import Field

from lx_dtypes.models.base_models.person import Person
from lx_dtypes.utils.factories.field_defaults import str_unknown_factory


class ExaminerShallowDataDict(TypedDict):
    first_name: Optional[str]
    last_name: str
    dob: NotRequired[Optional[date]]
    center_name: str
    gender: NotRequired[Optional[str]]
    uuid: NotRequired[str]


class ExaminerDataDict(TypedDict):
    first_name: Optional[str]
    last_name: str
    dob: NotRequired[Optional[date]]
    center_name: str
    gender: NotRequired[Optional[str]]
    external_ids: Optional[Dict[str, str]]
    uuid: NotRequired[str]


class ExaminerShallow(Person):
    center_name: str = Field(default_factory=str_unknown_factory)

    @property
    def ddict_shallow(self) -> type[ExaminerShallowDataDict]:
        return ExaminerShallowDataDict

    def to_ddict_shallow(self) -> ExaminerShallowDataDict:
        """Convert the ExaminerShallow instance to an ExaminerShallowDataDict.

        Returns:
            ExaminerShallowDataDict: The converted shallow data dictionary.
        """
        data_dict = self.ddict_shallow(**self.model_dump())
        return data_dict


class Examiner(ExaminerShallow):
    external_ids: Dict[str, str] = Field(default_factory=dict)

    @property
    def ddict(self) -> type[ExaminerDataDict]:
        return ExaminerDataDict

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

    def to_ddict(self) -> ExaminerDataDict:
        """Convert the Examiner instance to an ExaminerDataDict.

        Returns:
            ExaminerDataDict: The converted data dictionary.
        """
        data_dict = self.ddict(**self.model_dump())
        return data_dict

    def to_ddict_shallow(self) -> ExaminerShallowDataDict:
        """Convert the Examiner instance to an ExaminerShallowDataDict.

        Returns:
            ExaminerShallowDataDict: The converted shallow data dictionary.
        """
        dump = self.model_dump()
        shallow_data = {
            key: dump[key]
            for key in self.ddict_shallow.__annotations__.keys()
            if key in dump
        }
        return self.ddict_shallow(**shallow_data)
