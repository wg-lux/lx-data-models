from datetime import datetime, timezone
from pydantic import BaseModel, AwareDatetime


class Person(BaseModel):
    first_name: str
    last_name: str
    dob: date
    email: str
