from lx_dtypes.models.contracts.authz import validate_keycloak_claims


def test_keycloak_claims_normalize_group_paths() -> None:
    claims = validate_keycloak_claims(
        {
            "sub": "subject-1",
            "groups": [
                "centers/center-a",
                "/centers/center-a/",
                " /centers/center-b ",
                "",
            ],
        }
    )

    assert claims.groups == ["/centers/center-a", "/centers/center-b"]
