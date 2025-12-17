from typing import cast

from ninja.testing import TestClient
from pytest import fixture

from lx_dtypes.contrib.lx_django.api import api
from lx_dtypes.contrib.lx_django.api.stubs import TypedNinjaAPIClient

# https://docs.djangoproject.com/en/5.2/topics/testing/tools


@fixture(scope="session")
def ninja_test_client() -> TypedNinjaAPIClient:
    client = cast(TypedNinjaAPIClient, TestClient(api))
    return client
