from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .json_types import JsonValue


class KeycloakRoleContainerPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    roles: list[str] = Field(default_factory=list)


class KeycloakClaimsPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    preferred_username: str = ""
    sub: str = ""
    email: str = ""
    given_name: str = ""
    family_name: str = ""
    roles: list[str] = Field(default_factory=list)
    realm_access: KeycloakRoleContainerPayload = Field(
        default_factory=KeycloakRoleContainerPayload
    )
    resource_access: dict[str, KeycloakRoleContainerPayload] = Field(
        default_factory=dict
    )

    @field_validator("preferred_username", "sub", "email", "given_name", "family_name")
    @classmethod
    def strip_claim_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def require_subject_identifier(self) -> "KeycloakClaimsPayload":
        if not self.preferred_username and not self.sub:
            raise ValueError("preferred_username or sub is required")
        return self

    @property
    def username(self) -> str:
        return self.preferred_username or self.sub

    @property
    def role_names(self) -> set[str]:
        roles = set(self.roles)
        roles.update(self.realm_access.roles)
        for resource_entry in self.resource_access.values():
            roles.update(resource_entry.roles)
        return {role for role in roles if role}


class KeycloakTokenResponsePayload(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, strict=True)

    access_token: str = Field(min_length=1)
    refresh_token: str = ""


def validate_keycloak_claims(
    payload: Mapping[str, JsonValue],
) -> KeycloakClaimsPayload:
    return KeycloakClaimsPayload.model_validate(dict(payload))


def validate_keycloak_token_response(
    payload: Mapping[str, JsonValue],
) -> KeycloakTokenResponsePayload:
    return KeycloakTokenResponsePayload.model_validate(dict(payload))


__all__ = [
    "KeycloakClaimsPayload",
    "KeycloakRoleContainerPayload",
    "KeycloakTokenResponsePayload",
    "validate_keycloak_claims",
    "validate_keycloak_token_response",
]
