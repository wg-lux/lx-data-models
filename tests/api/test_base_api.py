from lx_dtypes.lx_django.api.stubs import TypedNinjaAPIClient

# https://docs.djangoproject.com/en/5.2/topics/testing/tools/


class TestBaseAPI:
    def test_hello_world_route(self, ninja_test_client: TypedNinjaAPIClient) -> None:
        client = ninja_test_client
        response = client.get("/hello")

        assert response.status_code == 200

        # 3. response.json() is built-in and ready to use
        assert response.json() == "Hello world"
