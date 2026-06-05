from __future__ import annotations

import json
import os
import posixpath
import shutil
import uuid
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Protocol,
    TypeVar,
    cast,
)

from django.conf import settings
from ninja.errors import HttpError  # type: ignore[import-untyped]
from pydantic import BaseModel
import yaml

from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    KnowledgeBaseRegistryError,
    clear_knowledge_base_resolver_caches,
    load_knowledge_base,
)
from lx_dtypes.models.knowledge_base import KB_MODEL_NAMES_ORDERED
from lx_dtypes.utils.parser import camel_to_snake

from .lookup_tracker import register_runtime_lookup_tracker
from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])


if TYPE_CHECKING:
    Schema = BaseModel
    File = cast(Any, object())
    from ninja.files import UploadedFile
else:
    from ninja import File
    from ninja import Schema
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
    input_dirs: List[str]
    is_active: bool = False


class TerminologyBundleListResponse(Schema):
    registry_path: str
    active: TerminologyBundleVersion | None
    bundles: List[TerminologyBundleVersion]


class SelectTerminologyBundleRequest(Schema):
    module_name: str
    version: str


class SelectTerminologyBundleResponse(Schema):
    ok: bool
    active: TerminologyBundleVersion
    counts: Dict[str, int]


class ImportTerminologyBundleResponse(Schema):
    ok: bool
    imported: TerminologyBundleVersion
    registry_path: str
    counts: Dict[str, int]


_ACTIVE_TERMINOLOGY_SELECTION: tuple[str, str] | None = None


@dataclass(frozen=True)
class TerminologyRegistryEntry:
    input_dirs: tuple[str, ...]
    medical_field: str | None = None


def active_terminology_selection() -> tuple[str, str] | None:
    return _ACTIVE_TERMINOLOGY_SELECTION


def _settings_or_env(name: str) -> str:
    return str(getattr(settings, name, "") or os.getenv(name, "")).strip()


def _configured_terminology_registry_path() -> Path:
    configured = _settings_or_env("LX_DTYPES_TERMINOLOGY_REGISTRY")
    if not configured:
        configured = _settings_or_env("LX_DTYPES_KB_REGISTRY")
    if not configured:
        raise HttpError(
            404,
            "No terminology registry configured. Set LX_DTYPES_TERMINOLOGY_REGISTRY "
            "or LX_DTYPES_KB_REGISTRY.",
        )
    return Path(configured).expanduser().resolve()


def terminology_registry_path() -> Path:
    registry_path = _configured_terminology_registry_path()
    if not registry_path.exists():
        raise HttpError(404, f"Terminology registry does not exist: {registry_path}")
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


def _coerce_input_dirs(raw_entry: object) -> tuple[str, ...]:
    if isinstance(raw_entry, str):
        return (str(Path(raw_entry).expanduser().resolve()),)
    if isinstance(raw_entry, list):
        resolved: list[str] = []
        for item in raw_entry:
            if not isinstance(item, str):
                raise KnowledgeBaseRegistryError(
                    "Registry input_dirs entries must be strings."
                )
            resolved.append(str(Path(item).expanduser().resolve()))
        if not resolved:
            raise KnowledgeBaseRegistryError(
                "Registry input_dirs entries must not be empty."
            )
        return tuple(resolved)
    if isinstance(raw_entry, Mapping):
        if "input_dirs" in raw_entry:
            return _coerce_input_dirs(raw_entry["input_dirs"])
        for key in ("data_root", "path"):
            if key in raw_entry:
                return _coerce_input_dirs(raw_entry[key])
    raise KnowledgeBaseRegistryError(
        "Registry entries must be a path string, a list of path strings, "
        "or an object containing `input_dirs`, `data_root`, or `path`."
    )


def _normalize_medical_field(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise KnowledgeBaseRegistryError(
            "Registry medical_field entries must be strings."
        )
    normalized = value.strip()
    return normalized or None


def _coerce_registry_entry(raw_entry: object) -> TerminologyRegistryEntry:
    medical_field = None
    if isinstance(raw_entry, Mapping) and "medical_field" in raw_entry:
        medical_field = _normalize_medical_field(raw_entry["medical_field"])
    return TerminologyRegistryEntry(
        input_dirs=_coerce_input_dirs(raw_entry),
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
        except Exception:
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
            registry[(module_name, version)] = _coerce_registry_entry(raw_entry)
    return registry


def _active_selection_from_env() -> tuple[str, str] | None:
    module_name = _settings_or_env("LX_DTYPES_ACTIVE_TERMINOLOGY_MODULE")
    version = _settings_or_env("LX_DTYPES_ACTIVE_TERMINOLOGY_VERSION")
    if module_name and version:
        return module_name, version
    return _ACTIVE_TERMINOLOGY_SELECTION


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
        input_dirs=list(entry.input_dirs),
        is_active=active == (module_name, version),
    )


def _set_active_selection(
    *,
    registry_path: Path,
    module_name: str,
    version: str,
    medical_field: str | None,
) -> None:
    global _ACTIVE_TERMINOLOGY_SELECTION
    _ACTIVE_TERMINOLOGY_SELECTION = (module_name, version)
    os.environ["LX_DTYPES_KB_REGISTRY"] = str(registry_path)
    os.environ["LX_DTYPES_FINDINGS_MODULE"] = module_name
    os.environ["LX_DTYPES_ACTIVE_TERMINOLOGY_MODULE"] = module_name
    os.environ["LX_DTYPES_ACTIVE_TERMINOLOGY_VERSION"] = version
    if medical_field:
        os.environ["LX_DTYPES_ACTIVE_MEDICAL_FIELD"] = medical_field
    else:
        os.environ.pop("LX_DTYPES_ACTIVE_MEDICAL_FIELD", None)
    clear_knowledge_base_resolver_caches()


def _record_counts(kb: Any) -> Dict[str, int]:
    record_lists = kb.export_record_lists()
    counts = {
        key: len(value)
        for key, value in record_lists.items()
        if isinstance(value, list)
    }
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
        or normalized.startswith("/")
        or normalized.startswith("../")
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
        raise HttpError(500, f"Terminology registry could not be read: {exc}") from exc
    if not isinstance(payload, dict):
        raise HttpError(500, "Terminology registry must be a JSON object.")
    modules = payload.setdefault("modules", {})
    if not isinstance(modules, dict):
        raise HttpError(
            500, "Terminology registry `modules` entry must be a JSON object."
        )
    return payload


def _register_imported_bundle(
    *,
    registry_path: Path,
    module_name: str,
    version: str,
    input_dir: Path,
    medical_field: str | None,
) -> TerminologyRegistryEntry:
    payload = _load_registry_payload_for_write(registry_path)
    modules = payload.setdefault("modules", {})
    module_versions = modules.setdefault(module_name, {})
    if not isinstance(module_versions, dict):
        raise HttpError(
            500, "Terminology registry module version map must be a JSON object."
        )

    entry: dict[str, Any] = {"input_dirs": [str(input_dir.resolve())]}
    if medical_field:
        entry["medical_field"] = medical_field
    module_versions[version] = entry
    registry_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    clear_knowledge_base_resolver_caches()
    return TerminologyRegistryEntry(
        input_dirs=(str(input_dir.resolve()),),
        medical_field=medical_field,
    )


def _validate_imported_bundle(
    *,
    module_name: str,
    input_dir: Path,
) -> Dict[str, int]:
    clear_knowledge_base_resolver_caches()
    try:
        kb = load_knowledge_base(module_name, input_dirs=[input_dir])
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
) -> tuple[str, str, str | None, Path, Dict[str, int]]:
    file_map = _strip_single_zip_root(_read_zip_file_map(upload))
    module_name, version, medical_field = _read_bundle_identity(file_map)

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
        if target_root.is_dir():
            shutil.rmtree(target_root)
        elif target_root.exists():
            target_root.unlink()
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
) -> Dict[str, Any]:
    kb = _load_registered_kb(
        registry_path=registry_path,
        module_name=bundle.module_name,
        version=bundle.version,
    )
    return kb.export_fhir_terminology(
        bundle=True,
        medical_field=bundle.medical_field,
    )


def _active_payload(
    registry: dict[tuple[str, str], TerminologyRegistryEntry],
) -> TerminologyBundleVersion | None:
    active = _active_selection_from_env()
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
) -> None:
    @api.get("/terminology/bundles")
    def list_terminology_bundles(
        request: BaseRequest,
    ) -> TerminologyBundleListResponse:
        del request
        try:
            registry_path = terminology_registry_path()
            registry = load_terminology_registry(registry_path)
        except KnowledgeBaseRegistryError as exc:
            raise HttpError(500, str(exc)) from exc

        active = _active_selection_from_env()
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
            registry_path=str(registry_path),
            active=_active_payload(registry),
            bundles=bundles,
        )

    @api.get("/terminology/active/fhir")
    def export_active_terminology_fhir(
        request: BaseRequest,
    ) -> Dict[str, Any]:
        del request
        try:
            registry_path = terminology_registry_path()
            registry = load_terminology_registry(registry_path)
        except KnowledgeBaseRegistryError as exc:
            raise HttpError(500, str(exc)) from exc

        active = _active_payload(registry)
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
                f"'{active.version}' could not be exported as FHIR: {exc}",
            ) from exc

    @api.get("/terminology/bundles/{module_name}/{version}/fhir")
    def export_terminology_bundle_fhir(
        request: BaseRequest,
        module_name: str,
        version: str,
    ) -> Dict[str, Any]:
        del request
        module_name = module_name.strip()
        version = version.strip()
        try:
            registry_path = terminology_registry_path()
            registry = load_terminology_registry(registry_path)
        except KnowledgeBaseRegistryError as exc:
            raise HttpError(500, str(exc)) from exc

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
            active=_active_selection_from_env(),
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
                f"be exported as FHIR: {exc}",
            ) from exc

    @api.post("/terminology/bundles/import")
    def import_terminology_bundle(
        request: BaseRequest,
        file: UploadedFile = File(...),
    ) -> ImportTerminologyBundleResponse:
        del request
        registry_path = _terminology_registry_path_for_write()
        module_name, version, medical_field, input_dir, counts = (
            _install_terminology_zip(
                upload=file,
                registry_path=registry_path,
            )
        )
        entry = _register_imported_bundle(
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
            active=(module_name, version),
        )
        _set_active_selection(
            registry_path=registry_path,
            module_name=module_name,
            version=version,
            medical_field=imported.medical_field,
        )
        clear_kb_caches()
        return ImportTerminologyBundleResponse(
            ok=True,
            imported=imported,
            registry_path=str(registry_path),
            counts=counts,
        )

    @api.post("/terminology/bundles/select")
    def select_terminology_bundle(
        request: BaseRequest,
        payload: SelectTerminologyBundleRequest,
    ) -> SelectTerminologyBundleResponse:
        del request
        module_name = payload.module_name.strip()
        version = payload.version.strip()
        try:
            registry_path = terminology_registry_path()
            registry = load_terminology_registry(registry_path)
        except KnowledgeBaseRegistryError as exc:
            raise HttpError(500, str(exc)) from exc

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
                f"Terminology bundle '{module_name}' version '{version}' could not be loaded: {exc}",
            ) from exc

        active_payload = _bundle_payload(
            module_name=module_name,
            version=version,
            entry=entry,
            active=(module_name, version),
        )

        _set_active_selection(
            registry_path=registry_path,
            module_name=module_name,
            version=version,
            medical_field=active_payload.medical_field,
        )
        clear_kb_caches()
        return SelectTerminologyBundleResponse(
            ok=True,
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
