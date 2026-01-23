from typing import Literal

from ninja import NinjaAPI

from .request_types import BaseRequest

api = NinjaAPI()


@api.get("/hello")
def hello(request: BaseRequest) -> Literal["Hello world"]:
    """
    Return the fixed greeting used as the /hello endpoint response.

    Returns:
        The exact string "Hello world" returned to clients.
    """
    return "Hello world"
