"""Explicit-path terminology service for the lx-dtypes contracts API.

No environment-variable reads/writes and no implicit provisioning on reads.
Registry writes retain the existing POSIX advisory-lock + atomic-replace model.
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import stat
import zipfile
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any, Protocol

import yaml

from lx_dtypes.knowledge_base_registry import (
    RegistryActiveIdentity,
    RegistryEntry,
    RegistryPayload,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
    load_knowledge_base,
    resolve_registry_entry_inputs,
)
from lx_dtypes.models.interface.remote_data_roots import (
    is_remote_data_root,
    resolve_remote_data_root,
)
from lx_dtypes.models.knowledge_base import KB_MODEL_NAMES_ORDERED
from lx_dtypes.utils.parser import camel_to_snake

from .terminology_schemas import (
    ImportTerminologyBundleResponse,
    SelectTerminologyBundleResponse,
    TerminologyBundleListResponse,
    TerminologyBundleVersion,
)

Identity = tuple[str, str]


class BinaryUpload(Protocol):
    def read(self, size: int = -1, /) -> bytes: ...


class TerminologyError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate registry key: {key!r}")
        result[key] = value
    return result


def _counts(kb: KnowledgeBase) -> dict[str, int]:
    # Retain the source file's record-list/core-concept compatibility.
    export = getattr(kb, "export_record_lists", None)
    if not callable(export):
        export = getattr(kb, "export_core_concepts", None)
    records = export() if callable(export) else {}
    counts = (
        {
            str(key): len(value)
            for key, value in records.items()
            if isinstance(value, list)
        }
        if isinstance(records, Mapping)
        else {}
    )
    for model in KB_MODEL_NAMES_ORDERED:
        name = camel_to_snake(model)
        value = getattr(kb, name, None)
        if isinstance(value, dict):
            counts[name] = len(value)
    return counts


def _safe_identity(value: object, label: str) -> str:
    name = str(value or "").strip()
    if not name or name in {".", ".."} or any(c in name for c in "/\\\0"):
        raise TerminologyError(
            400, f"Bundle {label} must be a non-empty path-safe value."
        )
    return name


@dataclass(frozen=True)
class TerminologyService:
    registry_path: Path
    max_zip_bytes: int = 32 * 1024 * 1024
    max_unpacked_bytes: int = 128 * 1024 * 1024
    max_files: int = 4096

    def __post_init__(self) -> None:
        if not self.registry_path.is_absolute():
            raise ValueError("registry_path must be absolute")
        if min(self.max_zip_bytes, self.max_unpacked_bytes, self.max_files) <= 0:
            raise ValueError("Upload limits must be positive")

    @property
    def import_root(self) -> Path:
        return self.registry_path.parent / "terminology-packages"

    def provision(self) -> None:
        """Hydrate editable shipped resources; preserve registered custom bundles."""
        from .hydration import hydrate_registry

        hydrate_registry(self)

    def active_identity(self) -> Identity | None:
        payload, _ = self._snapshot()
        return self._active(payload)

    def list_bundles(self) -> TerminologyBundleListResponse:
        payload, revision = self._snapshot()
        active = self._active(payload)
        bundles = [
            self._bundle((name, version), entry, active)
            for name, versions in sorted(payload.modules.items())
            for version, entry in sorted(versions.items())
        ]
        return TerminologyBundleListResponse(
            revision=revision,
            active=next((bundle for bundle in bundles if bundle.is_active), None),
            bundles=bundles,
        )

    def load(self, module_name: str, version: str) -> KnowledgeBase:
        payload, _ = self._snapshot()
        identity = module_name, version
        return self._load(identity, self._entry(payload, identity))

    def export_fhir(self, identity: Identity | None = None) -> dict[str, Any]:
        payload, _ = self._snapshot()
        active = self._active(payload)
        identity = identity if identity is not None else active
        if identity is None:
            raise TerminologyError(404, "No active terminology bundle is selected.")
        entry = self._entry(payload, identity)
        kb = self._load(identity, entry)
        bundle = self._bundle(identity, entry, active)
        try:
            result = kb.export_fhir_terminology(
                bundle=True,
                medical_field=bundle.medical_field,
            )
        except (ValueError, RuntimeError, OSError) as exc:
            raise TerminologyError(
                409,
                "Terminology bundle could not be exported as FHIR.",
            ) from exc
        if not isinstance(result, dict):
            raise TypeError("FHIR bundle export must return a mapping")
        return result

    def select(
        self,
        module_name: str,
        version: str,
        *,
        expected_revision: str,
        on_selected: Callable[[KnowledgeBase], object],
        clear_application_caches: Callable[[], None],
    ) -> SelectTerminologyBundleResponse:
        identity = module_name, version
        with self._lock():
            payload, revision = self._snapshot()
            if revision != expected_revision:
                raise TerminologyError(
                    409, "Registry changed; reload bundles before selecting."
                )
            entry = self._entry(payload, identity)
            kb = self._load(identity, entry)
            bundle, counts = self._bundle(identity, entry, identity), _counts(kb)
            payload.active = RegistryActiveIdentity(
                module_name=module_name, version=version
            )
            revision = self._write(payload)
            # No tracker/cache side effects for a rejected compare-and-swap.
            # Keep callbacks under the writer lock so concurrent selections cannot reorder them.
            clear_knowledge_base_resolver_caches()
            clear_application_caches()
            on_selected(kb)
        return SelectTerminologyBundleResponse(
            ok=True,
            revision=revision,
            active=bundle,
            counts=counts,
        )

    def import_zip(self, upload: BinaryUpload) -> ImportTerminologyBundleResponse:
        files = self._zip_files(upload)
        try:
            config = yaml.safe_load(files["config.yaml"].decode("utf-8"))
        except (KeyError, UnicodeError, yaml.YAMLError) as exc:
            raise TerminologyError(
                400, "ZIP requires a valid UTF-8 root config.yaml."
            ) from exc
        if not isinstance(config, Mapping):
            raise TerminologyError(400, "config.yaml must contain an object.")
        name = _safe_identity(config.get("name"), "name")
        version = _safe_identity(config.get("version"), "version")
        medical_field = self._medical_field(config.get("medical_field"), status=400)
        identity = name, version
        self.import_root.mkdir(parents=True, exist_ok=True)
        # Hash the identity for storage; unlike character replacement, this does not
        # collapse distinct names (e.g. A+B and A_B) onto the same directory.
        token = sha256(json.dumps(identity, ensure_ascii=True).encode()).hexdigest()
        destination = self.import_root / token
        with TemporaryDirectory(prefix=".staging-", dir=self.import_root) as temporary:
            staged = Path(temporary)
            for relative, content in files.items():
                target = staged / name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            self._load_paths(identity, [staged])
            with self._lock():
                payload, _ = self._snapshot(allow_missing=True)
                versions = payload.modules.setdefault(name, {})
                if version in versions or destination.exists():
                    raise TerminologyError(
                        409,
                        "This bundle identity is already registered or installed.",
                    )
                staged.rename(destination)
                try:
                    kb = self._load_paths(identity, [destination])
                    counts = _counts(kb)
                    entry = RegistryEntry.model_validate(
                        {
                            "sources": [
                                {"kind": "filesystem", "input_dirs": [str(destination)]}
                            ],
                            "medical_field": medical_field,
                        }
                    )
                    versions[version] = entry
                    imported = self._bundle(identity, entry, self._active(payload))
                    revision = self._write(payload)
                except Exception:
                    # The registry was not committed; do not leave an installed orphan.
                    shutil.rmtree(destination, ignore_errors=True)
                    raise
        clear_knowledge_base_resolver_caches()
        return ImportTerminologyBundleResponse(
            ok=True,
            revision=revision,
            imported=imported,
            counts=counts,
        )

    def _snapshot(self, *, allow_missing: bool = False) -> tuple[RegistryPayload, str]:
        try:
            data = self.registry_path.read_bytes()
        except FileNotFoundError as exc:
            if not allow_missing:
                raise TerminologyError(
                    404,
                    "Terminology registry does not exist; provision it first.",
                ) from exc
            return RegistryPayload(modules={}), f"sha256:{sha256(b'').hexdigest()}"
        except OSError as exc:
            raise TerminologyError(
                500, "Terminology registry could not be read."
            ) from exc
        try:
            raw = json.loads(data, object_pairs_hook=_unique_keys)
            # Normalize old path/list/data_root entries before using the package schema.
            if not isinstance(raw, dict):
                raise TypeError("Registry must contain an object")
            raw = raw if "modules" in raw else {"modules": raw}
            if not isinstance(raw["modules"], dict):
                raise TypeError("Registry modules must contain an object")
            for name, versions in raw["modules"].items():
                if (
                    not isinstance(name, str)
                    or not name.strip()
                    or not isinstance(versions, dict)
                ):
                    raise ValueError("Invalid registry module")
                for version, entry in versions.items():
                    if not isinstance(version, str) or not version.strip():
                        raise ValueError("Invalid registry version")
                    if isinstance(entry, (str, list)):
                        entry = {"input_dirs": entry}
                    if isinstance(entry, dict) and "sources" not in entry:
                        key = next(
                            (
                                key
                                for key in ("input_dirs", "data_root", "path")
                                if key in entry
                            ),
                            None,
                        )
                        if key is not None:
                            value = entry[key]
                            entry = {
                                **entry,
                                "input_dirs": [value]
                                if isinstance(value, str)
                                else value,
                            }
                    versions[version] = entry
            payload = RegistryPayload.model_validate(raw)
        except (ValueError, UnicodeError) as exc:
            raise TerminologyError(500, "Terminology registry is invalid.") from exc
        return payload, f"sha256:{sha256(data).hexdigest()}"

    @staticmethod
    def _active(payload: RegistryPayload) -> Identity | None:
        return (
            (payload.active.module_name, payload.active.version)
            if payload.active
            else None
        )

    @staticmethod
    def _entry(payload: RegistryPayload, identity: Identity) -> RegistryEntry:
        try:
            return payload.modules[identity[0]][identity[1]]
        except KeyError as exc:
            raise TerminologyError(
                404,
                f"Bundle '{identity[0]}@{identity[1]}' is not registered.",
            ) from exc

    @staticmethod
    def _medical_field(value: object, *, status: int = 500) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TerminologyError(status, "medical_field must be a string.")
        return value.strip() or None

    def _bundle(
        self,
        identity: Identity,
        entry: RegistryEntry,
        active: Identity | None,
    ) -> TerminologyBundleVersion:
        medical_field = self._medical_field(
            (entry.model_extra or {}).get("medical_field")
        )
        if medical_field is None:
            # Legacy entries may omit metadata. Remote URLs are not filesystem paths.
            for value in self._source_inputs(identity, entry):
                if is_remote_data_root(value):
                    continue
                config_path = Path(value) / identity[0] / "config.yaml"
                if not config_path.is_file():
                    continue
                try:
                    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                    if isinstance(config, Mapping):
                        field = config.get("medical_field")
                        medical_field = (
                            (field.strip() or None) if isinstance(field, str) else None
                        )
                except (OSError, UnicodeError, yaml.YAMLError):
                    pass
                break
        return TerminologyBundleVersion(
            module_name=identity[0],
            version=identity[1],
            medical_field=medical_field,
            is_active=identity == active,
        )

    @staticmethod
    def _source_inputs(identity: Identity, entry: RegistryEntry) -> tuple[str, ...]:
        raw = entry.model_dump(exclude_none=True)
        sources = raw.get("sources") or [
            {"kind": "filesystem", "input_dirs": raw.get("input_dirs", [])},
        ]
        for source in sources:
            if source["kind"] == "filesystem":
                for value in source["input_dirs"]:
                    if not is_remote_data_root(value) and not Path(value).is_absolute():
                        raise TerminologyError(
                            500,
                            "Registry filesystem inputs must be absolute paths.",
                        )
        try:
            return resolve_registry_entry_inputs(*identity, raw)
        except (LookupError, ValueError, OSError, RuntimeError) as exc:
            raise TerminologyError(
                409,
                "Registered bundle resources could not be resolved.",
            ) from exc

    def _load(self, identity: Identity, entry: RegistryEntry) -> KnowledgeBase:
        try:
            paths = [
                resolve_remote_data_root(value, module_name=identity[0])
                if is_remote_data_root(value)
                else Path(value)
                for value in self._source_inputs(identity, entry)
            ]
        except (ValueError, RuntimeError, OSError) as exc:
            raise TerminologyError(
                409,
                "Registered bundle resources could not be resolved.",
            ) from exc
        return self._load_paths(identity, paths)

    @staticmethod
    def _load_paths(identity: Identity, paths: list[Path]) -> KnowledgeBase:
        if not paths or any(not path.is_absolute() for path in paths):
            raise TerminologyError(
                500, "Bundle inputs must be explicit absolute paths."
            )
        try:
            kb = load_knowledge_base(identity[0], version=identity[1], input_dirs=paths)
        except (LookupError, ValueError, RuntimeError, OSError, yaml.YAMLError) as exc:
            raise TerminologyError(
                409,
                f"Bundle '{identity[0]}@{identity[1]}' could not be loaded.",
            ) from exc
        if not isinstance(kb, KnowledgeBase):
            raise TypeError("Knowledge-base loader returned an unexpected type")
        return kb

    @contextmanager
    def _lock(self) -> Iterator[None]:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with self.registry_path.with_name(f".{self.registry_path.name}.lock").open(
            "a+b"
        ) as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def _write(self, payload: RegistryPayload) -> str:
        # Validate assignment/mutations too; Pydantic assignment validation is not enabled upstream.
        payload = RegistryPayload.model_validate(payload.model_dump(exclude_none=True))
        encoded = json.dumps(
            payload.model_dump(mode="json", exclude_none=True),
            indent=2,
            sort_keys=True,
        )
        data = (encoded + "\n").encode()
        temporary: Path | None = None
        committed = False
        try:
            with NamedTemporaryFile(
                dir=self.registry_path.parent,
                prefix=f".{self.registry_path.name}.",
                delete=False,
            ) as out:
                temporary = Path(out.name)
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temporary, self.registry_path)
            committed = True
        finally:
            if temporary is not None and not committed:
                temporary.unlink(missing_ok=True)
        return f"sha256:{sha256(data).hexdigest()}"

    def _zip_files(self, upload: BinaryUpload) -> dict[str, bytes]:
        try:
            content = upload.read(self.max_zip_bytes + 1)
        except (OSError, ValueError) as exc:
            raise TerminologyError(400, "Terminology ZIP could not be read.") from exc
        if len(content) > self.max_zip_bytes:
            raise TerminologyError(413, "Terminology ZIP exceeds the upload limit.")
        files: dict[str, bytes] = {}
        directories: set[str] = set()
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                if len(archive.infolist()) > self.max_files:
                    raise TerminologyError(
                        413, "Terminology ZIP contains too many entries."
                    )
                remaining = self.max_unpacked_bytes
                for info in archive.infolist():
                    raw = info.orig_filename.replace("\\", "/")
                    path = PurePosixPath(raw)
                    if (
                        path.is_absolute()
                        or ".." in path.parts
                        or "\0" in raw
                        or not path.parts
                    ):
                        raise TerminologyError(400, "Unsafe ZIP entry path.")
                    if stat.S_ISLNK(info.external_attr >> 16):
                        raise TerminologyError(400, "ZIP symlinks are not supported.")
                    if (
                        info.is_dir()
                        or raw.endswith("/")
                        or path.parts[0] == "__MACOSX"
                        or path.name == ".DS_Store"
                    ):
                        continue
                    name = path.as_posix()
                    parents = {
                        parent.as_posix() for parent in path.parents if parent.parts
                    }
                    if (
                        name in files
                        or name in directories
                        or parents.intersection(files)
                    ):
                        raise TerminologyError(
                            400,
                            "ZIP contains duplicate or conflicting file paths.",
                        )
                    directories.update(parents)
                    if info.file_size > remaining:
                        raise TerminologyError(
                            413, "Unpacked terminology exceeds the size limit."
                        )
                    with archive.open(info) as source:
                        data = source.read(remaining + 1)
                    remaining -= len(data)
                    if remaining < 0:
                        raise TerminologyError(
                            413, "Unpacked terminology exceeds the size limit."
                        )
                    files[name] = data
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError) as exc:
            raise TerminologyError(
                400, "Terminology upload must be a readable ZIP file."
            ) from exc
        if "config.yaml" not in files and files:
            roots = {name.split("/", 1)[0] for name in files}
            if len(roots) == 1 and all("/" in name for name in files):
                files = {name.split("/", 1)[1]: value for name, value in files.items()}
        if "config.yaml" not in files:
            raise TerminologyError(
                400, "Terminology ZIP must contain a root config.yaml."
            )
        return files
