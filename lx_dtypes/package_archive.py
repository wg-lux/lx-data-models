"""Canonical bounded ZIP decoding shared by authoring and registry uploads."""

import stat
import zipfile
from io import BytesIO
from pathlib import PurePosixPath
from typing import Protocol


class BinaryUpload(Protocol):
    def read(self, size: int = -1, /) -> bytes: ...


class PackageArchiveError(ValueError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def package_member_path(raw: str) -> PurePosixPath:
    """Require portable relative paths, including on Windows hosts."""
    path = PurePosixPath(raw)
    if (
        path.is_absolute()
        or ".." in path.parts
        or "\0" in raw
        or "\\" in raw
        or ":" in raw
        or not path.parts
    ):
        raise PackageArchiveError(400, "Unsafe ZIP entry path.")
    return path


def read_bounded_zip(
    upload: BinaryUpload,
    *,
    max_zip_bytes: int = 32 * 1024 * 1024,
    max_unpacked_bytes: int = 128 * 1024 * 1024,
    max_files: int = 4096,
) -> dict[str, bytes]:
    if min(max_zip_bytes, max_unpacked_bytes, max_files) <= 0:
        raise ValueError("Upload limits must be positive")
    try:
        content = upload.read(max_zip_bytes + 1)
    except (OSError, ValueError) as exc:
        raise PackageArchiveError(400, "Terminology ZIP could not be read.") from exc
    if len(content) > max_zip_bytes:
        raise PackageArchiveError(413, "Terminology ZIP exceeds the upload limit.")
    files: dict[str, bytes] = {}
    directories: set[str] = set()
    entries: set[str] = set()
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            if len(archive.infolist()) > max_files:
                raise PackageArchiveError(
                    413, "Terminology ZIP contains too many entries."
                )
            remaining = max_unpacked_bytes
            for info in archive.infolist():
                raw = info.orig_filename
                path = package_member_path(raw)
                name = path.as_posix()
                if name in entries:
                    raise PackageArchiveError(
                        400, "ZIP contains duplicate entry paths."
                    )
                entries.add(name)
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise PackageArchiveError(400, "ZIP symlinks are not supported.")
                if info.is_dir() or raw.endswith("/"):
                    if name in files or any(
                        parent.as_posix() in files for parent in path.parents
                    ):
                        raise PackageArchiveError(
                            400, "ZIP contains conflicting paths."
                        )
                    directories.add(name)
                    continue
                if path.parts[0] == "__MACOSX" or path.name == ".DS_Store":
                    continue
                parents = {parent.as_posix() for parent in path.parents if parent.parts}
                if name in files or name in directories or parents.intersection(files):
                    raise PackageArchiveError(
                        400,
                        "ZIP contains duplicate or conflicting file paths.",
                    )
                directories.update(parents)
                if info.file_size > remaining:
                    raise PackageArchiveError(
                        413, "Unpacked terminology exceeds the size limit."
                    )
                with archive.open(info) as source:
                    data = source.read(remaining + 1)
                remaining -= len(data)
                if remaining < 0:
                    raise PackageArchiveError(
                        413, "Unpacked terminology exceeds the size limit."
                    )
                files[name] = data
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError) as exc:
        raise PackageArchiveError(
            400, "Terminology upload must be a readable ZIP file."
        ) from exc
    return files


def read_package_zip(
    upload: BinaryUpload,
    *,
    max_zip_bytes: int = 32 * 1024 * 1024,
    max_unpacked_bytes: int = 128 * 1024 * 1024,
    max_files: int = 4096,
) -> dict[str, bytes]:
    files = read_bounded_zip(
        upload,
        max_zip_bytes=max_zip_bytes,
        max_unpacked_bytes=max_unpacked_bytes,
        max_files=max_files,
    )
    if "config.yaml" not in files and files:
        roots = {name.split("/", 1)[0] for name in files}
        if len(roots) == 1 and all("/" in name for name in files):
            files = {name.split("/", 1)[1]: value for name, value in files.items()}
    if "config.yaml" not in files:
        raise PackageArchiveError(
            400, "Terminology ZIP must contain a root config.yaml."
        )
    return files
