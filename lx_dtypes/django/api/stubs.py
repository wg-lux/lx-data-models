from typing import Any, Protocol

from ninja.testing.client import NinjaResponse


class TypedNinjaAPIClient(Protocol):  # minimal protocol to satisfy Pylance typing
    def get(
        self, path: str, data: dict[str, Any] | None = None, **request_params: Any
    ) -> NinjaResponse: ...
