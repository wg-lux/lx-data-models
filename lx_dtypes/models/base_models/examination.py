from datetime import date
from typing import Optional

from pydantic import AwareDatetime, BaseModel


class BaseExamination(BaseModel):
    name: str
    date: Optional[date]
    start_time: Optional[AwareDatetime]
    end_time: Optional[AwareDatetime]
    description: Optional[str] = None
