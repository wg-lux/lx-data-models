from __future__ import annotations

import hashlib
import json
import logging
import os
import stat
import uuid
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Callable
from urllib.parse import quote, urlparse

import requests  # type: ignore[import-untyped]

_MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
_MAX_EXTRACTED_BYTES = 256 * 1024 * 1024
_MAX_ARCHIVE_FILES = 4096

logger = logging.getLogger(__name__)


class RemoteDataRootError(ValueError):
    """Raised when a remote knowledge-base source cannot be resolved safely."""


@dataclass(frozen=True)
class GitHubTreeSource:
    owner: str
    repository: str
    ref: str
    tree_path: PurePosixPath


@dataclass(frozen=True)
class FilesystemOperations:
    atomic_move_path: Callable[..., Path]
    atomic_write_file: Callable[..., Path]
    ensure_directory: Callable[..., Path]
    safe_rmtree: Callable[..., None]


def _filesystem_operations() -> FilesystemOperations:
    try:
        from endoreg_db.utils.file_operations import (  # type: ignore[import-not-found]
            atomic_move_path,
            atomic_write_file,
            ensure_directory,
            safe_rmtree,
        )
    except ImportError as exc:
        raise RemoteDataRootError(
            "Remote knowledge-base materialization requires the audited "
            "endoreg_db filesystem adapter."
        ) from exc
    return FilesystemOperations(
        atomic_move_path=atomic_move_path,
        atomic_write_file=atomic_write_file,
        ensure_directory=ensure_directory,
        safe_rmtree=safe_rmtree,
    )


def _emit_event(*, status: str, source_url: str, detail: str = "") -> None:
    logger.info(
        json.dumps(
            {
                "event": "lx_dtypes.remote_data_root",
                "status": status,
                "source_url": source_url,
                "detail": detail,
            },
            sort_keys=True,
        )
    )


def parse_github_tree_url(source_url: str) -> GitHubTreeSource:
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise RemoteDataRootError(
            "Remote knowledge-base sources must use an HTTPS github.com tree URL."
        )
    if parsed.query or parsed.fragment:
        raise RemoteDataRootError(
            "GitHub tree URLs must not contain query parameters or fragments."
        )

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 5 or parts[2] != "tree":
        raise RemoteDataRootError(
            "Expected a GitHub tree URL in the form "
            "https://github.com/OWNER/REPOSITORY/tree/REF/PATH."
        )

    owner, repository, _, ref, *tree_parts = parts
    tree_path = PurePosixPath(*tree_parts)
    if any(part in {"", ".", ".."} for part in tree_path.parts):
        raise RemoteDataRootError("GitHub tree paths must not contain traversal.")
    return GitHubTreeSource(
        owner=owner,
        repository=repository.removesuffix(".git"),
        ref=ref,
        tree_path=tree_path,
    )


def is_remote_data_root(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https"}


def normalize_registry_input(value: str) -> str:
    stripped = value.strip()
    if is_remote_data_root(stripped):
        parse_github_tree_url(stripped)
        return stripped
    return str(Path(stripped).expanduser().resolve())


def _cache_root() -> Path:
    configured = os.getenv("LX_DTYPES_REMOTE_CACHE_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    xdg_cache_home = os.getenv("XDG_CACHE_HOME", "").strip()
    base = (
        Path(xdg_cache_home).expanduser() if xdg_cache_home else Path.home() / ".cache"
    )
    return (base / "lx-dtypes" / "remote-data-roots").resolve()


def _download_archive(source: GitHubTreeSource) -> bytes:
    archive_url = (
        f"https://github.com/{quote(source.owner, safe='')}/"
        f"{quote(source.repository, safe='')}/archive/{quote(source.ref, safe='')}.zip"
    )
    try:
        response = requests.get(
            archive_url,
            allow_redirects=True,
            stream=True,
            timeout=(10, 60),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RemoteDataRootError(
            f"Could not download remote knowledge-base source: {type(exc).__name__}."
        ) from exc

    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > _MAX_ARCHIVE_BYTES:
            raise RemoteDataRootError(
                "Remote knowledge-base archive exceeds the compressed size limit."
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _safe_archive_members(
    archive: zipfile.ZipFile,
    *,
    source: GitHubTreeSource,
) -> tuple[str, list[zipfile.ZipInfo]]:
    files = [info for info in archive.infolist() if not info.is_dir()]
    if not files or len(files) > _MAX_ARCHIVE_FILES:
        raise RemoteDataRootError("Remote knowledge-base archive has an invalid size.")
    if sum(info.file_size for info in files) > _MAX_EXTRACTED_BYTES:
        raise RemoteDataRootError(
            "Remote knowledge-base archive exceeds the extracted size limit."
        )

    roots = {PurePosixPath(info.filename).parts[0] for info in files}
    if len(roots) != 1:
        raise RemoteDataRootError("Remote knowledge-base archive has no single root.")
    archive_root = next(iter(roots))
    wanted_root = PurePosixPath(archive_root) / source.tree_path.parent

    selected: list[zipfile.ZipInfo] = []
    for info in files:
        member_path = PurePosixPath(info.filename)
        if ".." in member_path.parts or member_path.is_absolute():
            raise RemoteDataRootError("Remote archive contains an unsafe path.")
        if stat.S_ISLNK(info.external_attr >> 16):
            raise RemoteDataRootError("Remote archive contains an unsupported symlink.")
        if member_path.is_relative_to(wanted_root):
            selected.append(info)
    if not selected:
        raise RemoteDataRootError("The GitHub tree path is absent from the archive.")
    return archive_root, selected


def _materialize_archive(
    *,
    source_url: str,
    source: GitHubTreeSource,
    destination: Path,
) -> Path:
    archive_bytes = _download_archive(source)
    filesystem = _filesystem_operations()
    filesystem.ensure_directory(destination.parent, dir_mode=0o750)
    temporary_root = destination.parent / f".{destination.name}.{uuid.uuid4().hex}"
    filesystem.ensure_directory(temporary_root, dir_mode=0o750)
    try:
        with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
            archive_root, members = _safe_archive_members(archive, source=source)
            for info in members:
                relative_path = PurePosixPath(info.filename).relative_to(archive_root)
                output_path = temporary_root.joinpath(*relative_path.parts)
                filesystem.atomic_write_file(
                    destination=output_path,
                    content=(archive.read(info),),
                    required_bytes=info.file_size,
                    file_mode=0o640,
                    dir_mode=0o750,
                )

        module_root = temporary_root.joinpath(*source.tree_path.parent.parts)
        if not (module_root / source.tree_path.name / "config.yaml").is_file():
            raise RemoteDataRootError(
                "The GitHub tree URL does not identify a knowledge-base module."
            )
        if destination.exists():
            filesystem.safe_rmtree(temporary_root)
        else:
            filesystem.atomic_move_path(
                source=temporary_root,
                destination=destination,
                dir_mode=0o750,
            )
        _emit_event(status="materialized", source_url=source_url)
    except Exception as exc:
        filesystem.safe_rmtree(temporary_root, missing_ok=True)
        _emit_event(status="error", source_url=source_url, detail=str(exc))
        if isinstance(exc, RemoteDataRootError):
            raise
        if isinstance(exc, zipfile.BadZipFile):
            raise RemoteDataRootError(
                "Remote knowledge-base source did not return a valid ZIP archive."
            ) from exc
        raise
    return destination.joinpath(*source.tree_path.parent.parts)


def resolve_remote_data_root(source_url: str, *, module_name: str) -> Path:
    source = parse_github_tree_url(source_url)
    if source.tree_path.name != module_name:
        raise RemoteDataRootError(
            f"GitHub tree URL must end with the registered module name '{module_name}'."
        )
    cache_key = hashlib.sha256(source_url.encode("utf-8")).hexdigest()
    destination = _cache_root() / cache_key
    resolved_root = destination.joinpath(*source.tree_path.parent.parts)
    if (resolved_root / module_name / "config.yaml").is_file():
        return resolved_root
    return _materialize_archive(
        source_url=source_url,
        source=source,
        destination=destination,
    )


__all__ = [
    "is_remote_data_root",
    "normalize_registry_input",
    "parse_github_tree_url",
    "RemoteDataRootError",
    "resolve_remote_data_root",
]
