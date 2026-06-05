from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

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


def validate_keycloak_claims(
    payload: Mapping[str, JsonValue],
) -> KeycloakClaimsPayload:
    return KeycloakClaimsPayload.model_validate(dict(payload))


__all__ = [
    "KeycloakClaimsPayload",
    "KeycloakRoleContainerPayload",
    "validate_keycloak_claims",
]
