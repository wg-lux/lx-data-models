from datetime import datetime, timezone

from pydantic import BaseModel, Field


class Log(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
