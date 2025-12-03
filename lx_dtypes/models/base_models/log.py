from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict

from pydantic import AwareDatetime, BaseModel, Field


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogScope(str, Enum):
    TESTS = "tests"
    SCRIPTS = "scripts"


class Log(BaseModel):
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message: str
    level: LogLevel = LogLevel.INFO
    scope: LogScope = LogScope.SCRIPTS
    context: Dict[str, Any] | None = None
