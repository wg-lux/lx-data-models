from __future__ import annotations

import fcntl
import json
import logging
import os
import posixpath
import shutil
import uuid
import zipfile
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Protocol,
    TypeVar,
    cast,
)

import yaml
from django.conf import settings
from ninja.errors import HttpError  # type: ignore[import-untyped]
from pydantic import BaseModel, Field

from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    KnowledgeBaseRegistryError,
    clear_knowledge_base_resolver_caches,
    get_knowledge_base_identity,
    load_knowledge_base,
    resolve_registry_entry_inputs,
)
from lx_dtypes.models.knowledge_base import KB_MODEL_NAMES_ORDERED
from lx_dtypes.utils.parser import camel_to_snake

from .lookup_tracker import register_runtime_lookup_tracker
from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])
logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    Schema = BaseModel
    File = cast(Any, object())
    from ninja.files import UploadedFile
else:
    from ninja import File, Schema
    from ninja.files import UploadedFile


class _RouteDecorator(Protocol):
    def __call__(self, func: F, /) -> F: ...


class _TypedApi(Protocol):
    def get(self, path: str, /) -> _RouteDecorator: ...

    def post(self, path: str, /) -> _RouteDecorator: ...


class TerminologyBundleVersion(Schema):
    module_name: str
    version: str
    medical_field: str | None = None
    is_active: bool = False


class TerminologyBundleListResponse(Schema):
    revision: str
    active: TerminologyBundleVersion | None
    bundles: list[TerminologyBundleVersion]


class SelectTerminologyBundleRequest(Schema):
    module_name: str
    version: str
    expected_revision: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class SelectTerminologyBundleResponse(Schema):
    ok: bool
    revision: str
    active: TerminologyBundleVersion
    counts: dict[str, int]


class ImportTerminologyBundleResponse(Schema):
    ok: bool
    revision: str
    imported: TerminologyBundleVersion
    counts: dict[str, int]


@dataclass(frozen=True)
class TerminologyRegistryEntry:
    input_dirs: tuple[str, ...]
    medical_field: str | None = None


def active_terminology_selection() -> tuple[str, str] | None:
    registry_path = terminology_registry_path()
    return _active_selection_from_registry(registry_path)


def _settings_or_env(name: str) -> str:
    return str(getattr(settings, name, "") or os.getenv(name, "")).strip()


def _configured_terminology_registry_path() -> Path:
    configured = _settings_or_env("LX_DTYPES_KB_REGISTRY")
    if not configured:
        raise HttpError(
            404,
            "No knowledge-base registry configured. Set LX_DTYPES_KB_REGISTRY.",
        )
    return Path(configured).expanduser().resolve()


def terminology_registry_path() -> Path:
    registry_path = _configured_terminology_registry_path()
    if not registry_path.exists():
        raise HttpError(404, "The configured terminology registry does not exist.")
    return registry_path


def _terminology_registry_path_for_write() -> Path:
    registry_path = _configured_terminology_registry_path()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    return registry_path


def _terminology_import_root(registry_path: Path) -> Path:
    configured = _settings_or_env("LX_DTYPES_TERMINOLOGY_IMPORT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return (registry_path.parent / "terminology-packages").resolve()


def _normalize_medical_field(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise KnowledgeBaseRegistryError(
            "Registry medical_field entries must be strings."
        )
    normalized = value.strip()
    return normalized or None


def _coerce_registry_entry(
    module_name: str,
    version: str,
    raw_entry: object,
) -> TerminologyRegistryEntry:
    medical_field = None
    if isinstance(raw_entry, Mapping) and "medical_field" in raw_entry:
        medical_field = _normalize_medical_field(raw_entry["medical_field"])
    return TerminologyRegistryEntry(
        input_dirs=resolve_registry_entry_inputs(module_name, version, raw_entry),
        medical_field=medical_field,
    )


def _medical_field_from_config(
    *,
    module_name: str,
    input_dirs: tuple[str, ...],
) -> str | None:
    for input_dir in input_dirs:
        config_path = Path(input_dir) / module_name / "config.yaml"
        if not config_path.exists():
            continue
        try:
            payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except (OSError, UnicodeError, yaml.YAMLError):
            return None
        if not isinstance(payload, Mapping):
            return None
        value = payload.get("medical_field")
        return value.strip() if isinstance(value, str) and value.strip() else None
    return None


def load_terminology_registry(
    registry_path: Path | None = None,
) -> dict[tuple[str, str], TerminologyRegistryEntry]:
    resolved_path = registry_path or terminology_registry_path()
    raw_payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(raw_payload, Mapping):
        raise KnowledgeBaseRegistryError("Terminology registry must be a JSON object.")
    raw_modules = raw_payload.get("modules", raw_payload)
    if not isinstance(raw_modules, Mapping):
        raise KnowledgeBaseRegistryError(
            "Terminology registry `modules` entry must be a JSON object."
        )

    registry: dict[tuple[str, str], TerminologyRegistryEntry] = {}
    for module_name, module_versions in raw_modules.items():
        if not isinstance(module_name, str) or not module_name.strip():
            raise KnowledgeBaseRegistryError(
                "Terminology registry module names must be non-empty strings."
            )
        if not isinstance(module_versions, Mapping):
            raise KnowledgeBaseRegistryError(
                "Terminology registry module version map must be a JSON object."
            )
        for version, raw_entry in module_versions.items():
            if not isinstance(version, str) or not version.strip():
                raise KnowledgeBaseRegistryError(
                    "Terminology registry versions must be non-empty strings."
                )
            registry[(module_name, version)] = _coerce_registry_entry(
                module_name, version, raw_entry
            )
    return registry


def _active_selection_from_registry(registry_path: Path) -> tuple[str, str] | None:
    raw_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(raw_payload, Mapping):
        raise KnowledgeBaseRegistryError("Terminology registry must be a JSON object.")
    raw_active = raw_payload.get("active")
    if raw_active is None:
        return None
    if not isinstance(raw_active, Mapping):
        raise KnowledgeBaseRegistryError(
            "Terminology registry `active` entry must be a JSON object."
        )
    module_name = raw_active.get("module_name")
    version = raw_active.get("version")
    if not isinstance(module_name, str) or not module_name.strip():
        raise KnowledgeBaseRegistryError(
            "Terminology registry active module_name must be a non-empty string."
        )
    if not isinstance(version, str) or not version.strip():
        raise KnowledgeBaseRegistryError(
            "Terminology registry active version must be a non-empty string."
        )
    selection = module_name.strip(), version.strip()
    if selection not in load_terminology_registry(registry_path):
        raise KnowledgeBaseRegistryError(
            "Terminology registry active selection must reference a registered bundle."
        )
    return selection


def _bundle_payload(
    *,
    module_name: str,
    version: str,
    entry: TerminologyRegistryEntry,
    active: tuple[str, str] | None,
) -> TerminologyBundleVersion:
    medical_field = entry.medical_field or _medical_field_from_config(
        module_name=module_name,
        input_dirs=entry.input_dirs,
    )
    return TerminologyBundleVersion(
        module_name=module_name,
        version=version,
        medical_field=medical_field,
        is_active=active == (module_name, version),
    )


def _set_active_selection(
    *,
    registry_path: Path,
    module_name: str,
    version: str,
    expected_revision: str,
) -> str:
    with _registry_write_lock(registry_path):
        current_revision = _registry_revision(registry_path)
        if expected_revision != current_revision:
            logger.warning(
                "Terminology registry compare-and-swap rejected",
                extra={
                    "event": "terminology_registry_revision_conflict",
                    "expected_revision": expected_revision,
                    "current_revision": current_revision,
                    "module_name": module_name,
                    "version": version,
                },
            )
            raise HttpError(
                409,
                "Terminology registry changed since it was read; reload bundles before selecting.",
            )
        payload = _load_registry_payload_for_write(registry_path)
        modules = payload.get("modules", {})
        versions = modules.get(module_name, {}) if isinstance(modules, Mapping) else {}
        if not isinstance(versions, Mapping) or version not in versions:
            raise HttpError(
                404,
                f"Terminology bundle '{module_name}' version '{version}' is not registered.",
            )
        payload["active"] = {"module_name": module_name, "version": version}
        _write_registry_payload_atomic(registry_path, payload)
        revision = _registry_revision(registry_path)
        logger.info(
            "Terminology active selection updated",
            extra={
                "event": "terminology_active_selection_updated",
                "previous_revision": current_revision,
                "revision": revision,
                "module_name": module_name,
                "version": version,
            },
        )
    clear_knowledge_base_resolver_caches()
    return revision


def _record_counts(kb: KnowledgeBase) -> dict[str, int]:
    counts: dict[str, int] = {}
    export_record_lists = getattr(kb, "export_record_lists", None)
    if callable(export_record_lists):
        record_lists = export_record_lists()
        if isinstance(record_lists, Mapping):
            counts.update(
                {
                    str(key): len(value)
                    for key, value in record_lists.items()
                    if isinstance(value, list)
                }
            )
    else:
        export_core_concepts = getattr(kb, "export_core_concepts", None)
        if callable(export_core_concepts):
            core_concepts = export_core_concepts()
            if isinstance(core_concepts, Mapping):
                counts.update(
                    {
                        str(key): len(value)
                        for key, value in core_concepts.items()
                        if isinstance(value, list)
                    }
                )
    for model_name in KB_MODEL_NAMES_ORDERED:
        attr_name = camel_to_snake(model_name)
        value = getattr(kb, attr_name, None)
        if isinstance(value, dict):
            counts[attr_name] = len(value)
    return counts


def _storage_segment(value: str) -> str:
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    normalized = "".join(char if char in allowed else "_" for char in value.strip())
    normalized = normalized.strip("._-")
    return normalized or "bundle"


def _assert_safe_name(value: str, label: str) -> str:
    normalized = value.strip()
    if (
        not normalized
        or normalized in {".", ".."}
        or "/" in normalized
        or "\\" in normalized
        or "\x00" in normalized
    ):
        raise HttpError(
            400,
            f"Terminology bundle {label} must be a non-empty path-safe value.",
        )
    return normalized


def _safe_zip_member_name(raw_name: str) -> str | None:
    name = raw_name.replace("\\", "/").strip()
    if not name or name.endswith("/"):
        return None
    if name.startswith("__MACOSX/") or name.endswith("/.DS_Store"):
        return None
    normalized = posixpath.normpath(name)
    if (
        not normalized
        or normalized == "."
        or normalized.startswith(("/", "../"))
        or "/../" in normalized
    ):
        raise HttpError(400, f"Unsafe ZIP entry path: {raw_name}")
    return normalized


def _read_zip_file_map(upload: UploadedFile) -> dict[str, bytes]:
    try:
        content = upload.read()
    except Exception as exc:
        raise HttpError(400, f"Terminology ZIP could not be read: {exc}") from exc

    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            file_map: dict[str, bytes] = {}
            for info in archive.infolist():
                member_name = _safe_zip_member_name(info.filename)
                if member_name is None:
                    continue
                file_map[member_name] = archive.read(info)
    except (RuntimeError, zipfile.BadZipFile) as exc:
        raise HttpError(400, "Terminology upload must be a valid ZIP file.") from exc

    if not file_map:
        raise HttpError(400, "Terminology ZIP does not contain any files.")
    return file_map


def _strip_single_zip_root(file_map: dict[str, bytes]) -> dict[str, bytes]:
    if "config.yaml" in file_map:
        return file_map

    roots = {
        path.split("/", 1)[0]
        for path in file_map
        if "/" in path and path.split("/", 1)[0]
    }
    if len(roots) != 1:
        return file_map

    root = next(iter(roots))
    stripped = {
        path[len(root) + 1 :]: content
        for path, content in file_map.items()
        if path.startswith(f"{root}/") and path[len(root) + 1 :]
    }
    return stripped if "config.yaml" in stripped else file_map


def _read_bundle_identity(
    file_map: dict[str, bytes],
) -> tuple[str, str, str | None]:
    config_content = file_map.get("config.yaml")
    if config_content is None:
        raise HttpError(400, "Terminology ZIP must contain a root config.yaml.")

    try:
        payload = yaml.safe_load(config_content.decode("utf-8")) or {}
    except UnicodeDecodeError as exc:
        raise HttpError(400, "Root config.yaml must be UTF-8 encoded.") from exc
    except Exception as exc:
        raise HttpError(400, f"Root config.yaml could not be parsed: {exc}") from exc

    if not isinstance(payload, Mapping):
        raise HttpError(400, "Root config.yaml must contain a YAML object.")

    module_name = _assert_safe_name(str(payload.get("name") or ""), "name")
    version = _assert_safe_name(str(payload.get("version") or ""), "version")
    medical_field = _normalize_medical_field(payload.get("medical_field"))
    return module_name, version, medical_field


def _write_imported_files(package_dir: Path, file_map: dict[str, bytes]) -> None:
    package_root = package_dir.resolve()
    for relative_name, content in file_map.items():
        destination = (package_dir / Path(relative_name)).resolve()
        if destination != package_root and package_root not in destination.parents:
            raise HttpError(400, f"Unsafe ZIP entry path: {relative_name}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)


def _load_registry_payload_for_write(registry_path: Path) -> dict[str, Any]:
    if not registry_path.exists():
        return {"modules": {}}

    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HttpError(500, "Terminology registry could not be read.") from exc
    if not isinstance(payload, dict):
        raise HttpError(500, "Terminology registry must be a JSON object.")
    modules = payload.setdefault("modules", {})
    if not isinstance(modules, dict):
        raise HttpError(
            500, "Terminology registry `modules` entry must be a JSON object."
        )
    return payload


def _write_registry_payload_atomic(
    registry_path: Path, payload: Mapping[str, Any]
) -> None:
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary_registry = registry_path.with_name(
        f".{registry_path.name}.{uuid.uuid4().hex}.tmp"
    )
    try:
        with temporary_registry.open("w", encoding="utf-8") as registry_file:
            registry_file.write(serialized)
            registry_file.flush()
            os.fsync(registry_file.fileno())
        os.replace(temporary_registry, registry_path)
    finally:
        temporary_registry.unlink(missing_ok=True)


def _registry_revision(registry_path: Path) -> str:
    payload = registry_path.read_bytes() if registry_path.exists() else b""
    return f"sha256:{sha256(payload).hexdigest()}"


@contextmanager
def _registry_write_lock(registry_path: Path) -> Any:
    lock_path = registry_path.with_name(f".{registry_path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _register_imported_bundle(
    *,
    registry_path: Path,
    module_name: str,
    version: str,
    input_dir: Path,
    medical_field: str | None,
) -> tuple[TerminologyRegistryEntry, str, tuple[str, str] | None]:
    with _registry_write_lock(registry_path):
        payload = _load_registry_payload_for_write(registry_path)
        modules = payload.setdefault("modules", {})
        module_versions = modules.setdefault(module_name, {})
        if not isinstance(module_versions, dict):
            raise HttpError(
                500, "Terminology registry module version map must be a JSON object."
            )
        if version in module_versions:
            raise HttpError(
                409,
                f"Terminology bundle '{module_name}' version '{version}' is already registered.",
            )

        entry: dict[str, Any] = {
            "sources": [
                {
                    "kind": "filesystem",
                    "input_dirs": [str(input_dir.resolve())],
                }
            ]
        }
        if medical_field:
            entry["medical_field"] = medical_field
        module_versions[version] = entry
        _write_registry_payload_atomic(registry_path, payload)
        revision = _registry_revision(registry_path)
        active = _active_selection_from_registry(registry_path)
    logger.info(
        "Terminology registry updated",
        extra={
            "event": "terminology_registry_updated",
            "module_name": module_name,
            "version": version,
            "revision": revision,
        },
    )
    clear_knowledge_base_resolver_caches()
    return (
        TerminologyRegistryEntry(
            input_dirs=(str(input_dir.resolve()),),
            medical_field=medical_field,
        ),
        revision,
        active,
    )


def _assert_import_identity_available(
    *,
    registry_path: Path,
    module_name: str,
    version: str,
) -> None:
    payload = _load_registry_payload_for_write(registry_path)
    modules = payload["modules"]
    module_versions = modules.get(module_name, {})
    if not isinstance(module_versions, dict):
        raise HttpError(
            500, "Terminology registry module version map must be a JSON object."
        )
    if version in module_versions:
        raise HttpError(
            409,
            f"Terminology bundle '{module_name}' version '{version}' is already registered.",
        )


def _validate_imported_bundle(
    *,
    module_name: str,
    input_dir: Path,
) -> dict[str, int]:
    clear_knowledge_base_resolver_caches()
    try:
        _, version = get_knowledge_base_identity(module_name, input_dirs=[input_dir])
        kb = load_knowledge_base(
            module_name,
            version=version,
            input_dirs=[input_dir],
        )
    except Exception as exc:
        raise HttpError(
            409,
            f"Terminology bundle '{module_name}' could not be loaded after import: {exc}",
        ) from exc
    return _record_counts(kb)


def _install_terminology_zip(
    *,
    upload: UploadedFile,
    registry_path: Path,
) -> tuple[str, str, str | None, Path, dict[str, int]]:
    file_map = _strip_single_zip_root(_read_zip_file_map(upload))
    module_name, version, medical_field = _read_bundle_identity(file_map)
    _assert_import_identity_available(
        registry_path=registry_path,
        module_name=module_name,
        version=version,
    )

    import_root = _terminology_import_root(registry_path)
    import_root.mkdir(parents=True, exist_ok=True)
    target_root = (
        import_root / _storage_segment(module_name) / _storage_segment(version)
    )
    tmp_root = (
        import_root / ".tmp" / f"{_storage_segment(module_name)}-{uuid.uuid4().hex}"
    )
    package_dir = tmp_root / module_name

    try:
        _write_imported_files(package_dir, file_map)
        _validate_imported_bundle(module_name=module_name, input_dir=tmp_root)
        target_root.parent.mkdir(parents=True, exist_ok=True)
        if target_root.exists():
            raise HttpError(
                409,
                f"Terminology bundle '{module_name}' version '{version}' is already installed.",
            )
        tmp_root.replace(target_root)
        counts = _validate_imported_bundle(
            module_name=module_name, input_dir=target_root
        )
    finally:
        if tmp_root.exists():
            shutil.rmtree(tmp_root, ignore_errors=True)

    return module_name, version, medical_field, target_root, counts


def _load_selected_kb(
    *,
    registry_path: Path,
    module_name: str,
    version: str,
) -> Any:
    previous_registry = os.environ.get("LX_DTYPES_KB_REGISTRY")
    os.environ["LX_DTYPES_KB_REGISTRY"] = str(registry_path)
    clear_knowledge_base_resolver_caches()
    try:
        kb = load_knowledge_base(module_name, version=version)
    except Exception:
        if previous_registry is None:
            os.environ.pop("LX_DTYPES_KB_REGISTRY", None)
        else:
            os.environ["LX_DTYPES_KB_REGISTRY"] = previous_registry
        clear_knowledge_base_resolver_caches()
        raise
    register_runtime_lookup_tracker(kb)
    return kb


def _load_registered_kb(
    *,
    registry_path: Path,
    module_name: str,
    version: str,
) -> Any:
    previous_registry = os.environ.get("LX_DTYPES_KB_REGISTRY")
    os.environ["LX_DTYPES_KB_REGISTRY"] = str(registry_path)
    clear_knowledge_base_resolver_caches()
    try:
        return load_knowledge_base(module_name, version=version)
    finally:
        if previous_registry is None:
            os.environ.pop("LX_DTYPES_KB_REGISTRY", None)
        else:
            os.environ["LX_DTYPES_KB_REGISTRY"] = previous_registry
        clear_knowledge_base_resolver_caches()


def _fhir_bundle_payload(
    *,
    registry_path: Path,
    bundle: TerminologyBundleVersion,
) -> dict[str, Any]:
    kb = _load_registered_kb(
        registry_path=registry_path,
        module_name=bundle.module_name,
        version=bundle.version,
    )
    payload = kb.export_fhir_terminology(
        bundle=True,
        medical_field=bundle.medical_field,
    )
    if not isinstance(payload, dict):
        raise TypeError("FHIR bundle export must return a mapping")
    return payload


def _active_payload(
    registry: dict[tuple[str, str], TerminologyRegistryEntry],
    *,
    registry_path: Path,
) -> TerminologyBundleVersion | None:
    active = _active_selection_from_registry(registry_path)
    if active is None:
        return None
    entry = registry.get(active)
    if entry is None:
        return None
    return _bundle_payload(
        module_name=active[0],
        version=active[1],
        entry=entry,
        active=active,
    )


def register_terminology_routes(
    api: _TypedApi,
    *,
    clear_kb_caches: Callable[[], None],
    authenticate_request_user: Callable[[BaseRequest], Any | None] | None = None,
    terminology_write_access_allowed: Callable[[object], bool] | None = None,
) -> None:
    def require_write_access(request: BaseRequest) -> None:
        if (
            authenticate_request_user is None
            or terminology_write_access_allowed is None
        ):
            return
        actor = authenticate_request_user(request)
        if actor is None:
            raise HttpError(401, "Authentication is required.")
        if not terminology_write_access_allowed(actor):
            raise HttpError(403, "Terminology write access is required.")

    @api.get("/terminology/bundles")
    def list_terminology_bundles(
        request: BaseRequest,
    ) -> TerminologyBundleListResponse:
        del request
        try:
            registry_path = terminology_registry_path()
            registry = load_terminology_registry(registry_path)
        except KnowledgeBaseRegistryError as exc:
            raise HttpError(500, "Terminology registry is invalid.") from exc

        active = _active_selection_from_registry(registry_path)
        bundles = [
            _bundle_payload(
                module_name=module_name,
                version=version,
                entry=entry,
                active=active,
            )
            for (module_name, version), entry in sorted(registry.items())
        ]
        return TerminologyBundleListResponse(
            revision=_registry_revision(registry_path),
            active=_active_payload(registry, registry_path=registry_path),
            bundles=bundles,
        )

    @api.get("/terminology/active/fhir")
    def export_active_terminology_fhir(
        request: BaseRequest,
    ) -> dict[str, Any]:
        del request
        try:
            registry_path = terminology_registry_path()
            registry = load_terminology_registry(registry_path)
        except KnowledgeBaseRegistryError as exc:
            raise HttpError(500, "Terminology registry is invalid.") from exc

        active = _active_payload(registry, registry_path=registry_path)
        if active is None:
            raise HttpError(404, "No active terminology bundle is selected.")

        try:
            return _fhir_bundle_payload(
                registry_path=registry_path,
                bundle=active,
            )
        except Exception as exc:
            raise HttpError(
                409,
                f"Active terminology bundle '{active.module_name}' version "
                f"'{active.version}' could not be exported as FHIR.",
            ) from exc

    @api.get("/terminology/bundles/{module_name}/{version}/fhir")
    def export_terminology_bundle_fhir(
        request: BaseRequest,
        module_name: str,
        version: str,
    ) -> dict[str, Any]:
        del request
        module_name = module_name.strip()
        version = version.strip()
        try:
            registry_path = terminology_registry_path()
            registry = load_terminology_registry(registry_path)
        except KnowledgeBaseRegistryError as exc:
            raise HttpError(500, "Terminology registry is invalid.") from exc

        entry = registry.get((module_name, version))
        if entry is None:
            raise HttpError(
                404,
                f"Terminology bundle '{module_name}' version '{version}' is not registered.",
            )

        bundle = _bundle_payload(
            module_name=module_name,
            version=version,
            entry=entry,
            active=_active_selection_from_registry(registry_path),
        )
        try:
            return _fhir_bundle_payload(
                registry_path=registry_path,
                bundle=bundle,
            )
        except Exception as exc:
            raise HttpError(
                409,
                f"Terminology bundle '{module_name}' version '{version}' could not "
                "be exported as FHIR.",
            ) from exc

    @api.post("/terminology/bundles/import")
    def import_terminology_bundle(
        request: BaseRequest,
        file: UploadedFile = File(...),  # noqa: B008 - Ninja request marker
    ) -> ImportTerminologyBundleResponse:
        require_write_access(request)
        registry_path = _terminology_registry_path_for_write()
        module_name, version, medical_field, input_dir, counts = (
            _install_terminology_zip(
                upload=file,
                registry_path=registry_path,
            )
        )
        entry, revision, active = _register_imported_bundle(
            registry_path=registry_path,
            module_name=module_name,
            version=version,
            input_dir=input_dir,
            medical_field=medical_field,
        )
        imported = _bundle_payload(
            module_name=module_name,
            version=version,
            entry=entry,
            active=active,
        )
        clear_kb_caches()
        return ImportTerminologyBundleResponse(
            ok=True,
            revision=revision,
            imported=imported,
            counts=counts,
        )

    @api.post("/terminology/bundles/select")
    def select_terminology_bundle(
        request: BaseRequest,
        payload: SelectTerminologyBundleRequest,
    ) -> SelectTerminologyBundleResponse:
        require_write_access(request)
        module_name = payload.module_name.strip()
        version = payload.version.strip()
        try:
            registry_path = terminology_registry_path()
            registry = load_terminology_registry(registry_path)
        except KnowledgeBaseRegistryError as exc:
            raise HttpError(500, "Terminology registry is invalid.") from exc

        entry = registry.get((module_name, version))
        if entry is None:
            raise HttpError(
                404,
                f"Terminology bundle '{module_name}' version '{version}' is not registered.",
            )

        try:
            kb = _load_selected_kb(
                registry_path=registry_path,
                module_name=module_name,
                version=version,
            )
        except Exception as exc:
            raise HttpError(
                409,
                f"Terminology bundle '{module_name}' version '{version}' could not be loaded.",
            ) from exc

        active_payload = _bundle_payload(
            module_name=module_name,
            version=version,
            entry=entry,
            active=(module_name, version),
        )

        revision = _set_active_selection(
            registry_path=registry_path,
            module_name=module_name,
            version=version,
            expected_revision=payload.expected_revision,
        )
        clear_kb_caches()
        return SelectTerminologyBundleResponse(
            ok=True,
            revision=revision,
            active=active_payload,
            counts=_record_counts(kb),
        )


__all__ = [
    "ImportTerminologyBundleResponse",
    "SelectTerminologyBundleRequest",
    "SelectTerminologyBundleResponse",
    "TerminologyBundleListResponse",
    "TerminologyBundleVersion",
    "active_terminology_selection",
    "load_terminology_registry",
    "register_terminology_routes",
    "terminology_registry_path",
]
