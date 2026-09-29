"""Immutable, content-addressed reference catalogue and provenance contract."""

import hashlib
import json
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .knowledge_base import KnowledgeBaseIdentity
from .reference_catalog import CatalogIdentity, ReferenceCatalogPayload, ReferenceKind


class ReferenceCatalogSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    identity: KnowledgeBaseIdentity
    projection: str = Field(default="all", min_length=1, max_length=2048)
    payload: ReferenceCatalogPayload
    snapshot_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @staticmethod
    def content_digest(
        identity: KnowledgeBaseIdentity,
        payload: ReferenceCatalogPayload,
        projection: str = "all",
    ) -> str:
        content = json.dumps(
            {
                "identity": identity.model_dump(mode="json"),
                "projection": projection,
                "payload": payload.model_dump(mode="json", by_alias=True),
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(content).hexdigest()

    @model_validator(mode="after")
    def validate_digest(self) -> Self:
        if self.snapshot_id != self.content_digest(
            self.identity, self.payload, self.projection
        ):
            raise ValueError("Reference catalogue content digest mismatch")
        keys = {record.key for record in self.payload.records}
        for record in self.payload.records:
            for field, kind, identity in record.references():
                if (kind, identity.name, identity.version) not in keys:
                    raise ValueError(
                        f"Unresolved reference {record.kind}.{record.identity.name}.{field}: {kind}.{identity.name}"
                    )
        return self


class CatalogBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: ReferenceKind
    identity: CatalogIdentity
    row_id: int = Field(gt=0)
    origin: Literal["created", "legacy_equivalent", "shared_import"]


class ReferenceCatalogReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["1.0"] = "1.0"
    snapshot: ReferenceCatalogSnapshot
    bindings: list[CatalogBinding]

    @model_validator(mode="after")
    def validate_bindings(self) -> Self:
        keys = [
            (item.kind, item.identity.name, item.identity.version)
            for item in self.bindings
        ]
        if len(keys) != len(set(keys)) or set(keys) != {
            record.key for record in self.snapshot.payload.records
        }:
            raise ValueError(
                "Receipt bindings must cover catalogue identities exactly once"
            )
        return self
