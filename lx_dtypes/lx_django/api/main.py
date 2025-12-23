from typing import Literal

from ninja import NinjaAPI

from .request_types import BaseRequest

api = NinjaAPI()


@api.get("/hello")
def hello(request: BaseRequest) -> Literal["Hello world"]:
    return "Hello world"
