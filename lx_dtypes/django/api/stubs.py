from typing import Any, Protocol

from ninja.testing.client import NinjaResponse


class TypedNinjaAPIClient(Protocol):  # minimal protocol to satisfy Pylance typing
    def get(
        self, path: str, data: dict[str, Any] | None = None, **request_params: Any
    ) -> NinjaResponse: """
        Perform a GET request to the given API path on a Ninja API client.
        
        Parameters:
            path (str): API path or endpoint to request.
            data (dict[str, Any] | None): Optional query or payload data to include with the request.
            **request_params (Any): Additional request parameters forwarded to the client (e.g., headers, params).
        
        Returns:
            NinjaResponse: The response object returned by the Ninja client.
        """
        ...