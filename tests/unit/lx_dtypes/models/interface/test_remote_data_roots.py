from __future__ import annotations

import errno
import shutil
import stat
import zipfile
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

from lx_dtypes.models.interface import remote_data_roots

_SOURCE_URL = (
    "https://github.com/wg-lux/lx-data-models/tree/main/demo-data/remote_demo_module"
)
_SOURCE = remote_data_roots.GitHubTreeSource(
    owner="wg-lux",
    repository="lx-data-models",
    ref="main",
    tree_path=PurePosixPath("demo-data/remote_demo_module"),
)


def _archive_bytes() -> bytes:
    archive_buffer = BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr(
            "lx-data-models-main/demo-data/remote_demo_module/config.yaml",
            "name: remote_demo_module\nversion: 0.1.0\n",
        )
    return archive_buffer.getvalue()


def _write_file(*, destination: Path, content: Any, **kwargs: Any) -> Path:
    del kwargs
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"".join(content))
    return destination


def _ensure_directory(path: Path, **kwargs: Any) -> Path:
    del kwargs
    path.mkdir(parents=True, exist_ok=True)
    return path


def _remove_tree(path: Path, *, missing_ok: bool = True) -> None:
    if path.exists():
        shutil.rmtree(path)
    elif not missing_ok:
        raise FileNotFoundError(path)


def test_safe_archive_members_rejects_symlinks() -> None:
    archive_buffer = BytesIO()
    link = zipfile.ZipInfo(
        "lx-data-models-main/demo-data/remote_demo_module/config.yaml"
    )
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr(link, "../../outside.yaml")

    with (
        zipfile.ZipFile(BytesIO(archive_buffer.getvalue())) as archive,
        pytest.raises(
            remote_data_roots.RemoteDataRootError,
            match="unsupported symlink",
        ),
    ):
        remote_data_roots._safe_archive_members(archive, source=_SOURCE)


@pytest.mark.parametrize(
    ("filename", "message"),
    [
        (
            "lx-data-models-main\\demo-data\\remote_demo_module\\config.yaml",
            "unsafe path separator",
        ),
        (
            "lx-data-models-main/demo-data/remote_demo_module/config.yaml",
            "duplicate file paths",
        ),
    ],
)
def test_safe_archive_members_rejects_ambiguous_paths(
    filename: str,
    message: str,
) -> None:
    archive_buffer = BytesIO()
    with zipfile.ZipFile(archive_buffer, "w") as archive:
        archive.writestr(filename, "first")
        if message == "duplicate file paths":
            archive.writestr(filename, "second")

    with (
        zipfile.ZipFile(BytesIO(archive_buffer.getvalue())) as archive,
        pytest.raises(remote_data_roots.RemoteDataRootError, match=message),
    ):
        remote_data_roots._safe_archive_members(archive, source=_SOURCE)


def test_ensure_directory_rejects_symlink_target(tmp_path: Path) -> None:
    real_directory = tmp_path / "real"
    real_directory.mkdir()
    linked_directory = tmp_path / "linked"
    linked_directory.symlink_to(real_directory, target_is_directory=True)

    with pytest.raises(OSError, match="not a real directory"):
        remote_data_roots._ensure_directory(linked_directory)


def test_safe_rmtree_refuses_symlink_without_touching_target(tmp_path: Path) -> None:
    real_directory = tmp_path / "real"
    real_directory.mkdir()
    sentinel = real_directory / "sentinel.txt"
    sentinel.write_text("keep")
    linked_directory = tmp_path / "linked"
    linked_directory.symlink_to(real_directory, target_is_directory=True)

    with pytest.raises(OSError, match="Refusing to recursively remove a symlink"):
        remote_data_roots._safe_rmtree(linked_directory)

    assert linked_directory.is_symlink()
    assert sentinel.read_text() == "keep"


def test_atomic_move_path_does_not_fallback_across_filesystems(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    sentinel = source / "sentinel.txt"
    sentinel.write_text("keep")
    destination = tmp_path / "destination"

    def cross_device_replace(source: Path, destination: Path) -> None:
        del source, destination
        raise OSError(errno.EXDEV, "Invalid cross-device link")

    monkeypatch.setattr(remote_data_roots.os, "replace", cross_device_replace)

    with pytest.raises(OSError) as exc_info:
        remote_data_roots._atomic_move_path(
            source=source,
            destination=destination,
        )

    assert exc_info.value.errno == errno.EXDEV
    assert sentinel.read_text() == "keep"
    assert not destination.exists()


def test_materialization_publishes_from_same_parent_without_cross_device_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cache" / "cache-key"
    move_calls: list[tuple[Path, Path]] = []

    def move_path(*, source: Path, destination: Path, **kwargs: Any) -> Path:
        del kwargs
        move_calls.append((source, destination))
        assert source.parent == destination.parent
        source.rename(destination)
        return destination

    monkeypatch.setattr(
        remote_data_roots,
        "_download_archive",
        lambda source: _archive_bytes(),
    )
    monkeypatch.setattr(
        remote_data_roots,
        "_filesystem_operations",
        lambda: remote_data_roots.FilesystemOperations(
            atomic_move_path=move_path,
            atomic_write_file=_write_file,
            ensure_directory=_ensure_directory,
            safe_rmtree=_remove_tree,
        ),
    )

    result = remote_data_roots._materialize_archive(
        source_url=_SOURCE_URL,
        source=_SOURCE,
        destination=destination,
    )

    assert result == destination / "demo-data"
    assert (result / "remote_demo_module" / "config.yaml").is_file()
    assert len(move_calls) == 1


@pytest.mark.parametrize(
    "poison", ["empty", "file", "symlink", "nested_symlink", "nested_file"]
)
def test_materialization_repairs_invalid_cache(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    poison: str,
) -> None:
    destination = tmp_path / "cache" / "cache-key"
    destination.parent.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("keep")
    if poison == "symlink":
        destination.symlink_to(outside, target_is_directory=True)
    elif poison == "file":
        destination.write_text("incomplete")
    else:
        destination.mkdir()
        if poison == "nested_symlink":
            (destination / "demo-data").symlink_to(outside, target_is_directory=True)
        elif poison == "nested_file":
            (destination / "demo-data").write_text("incomplete")
    monkeypatch.setattr(
        remote_data_roots, "_download_archive", lambda source: _archive_bytes()
    )
    assert (
        remote_data_roots._cached_module_root(destination=destination, source=_SOURCE)
        is None
    )
    result = remote_data_roots._materialize_archive(
        source_url=_SOURCE_URL,
        source=_SOURCE,
        destination=destination,
    )
    assert (result / "remote_demo_module" / "config.yaml").is_file()
    assert sentinel.read_text() == "keep"
    assert not destination.is_symlink()
    assert list(destination.parent.glob(f".{destination.name}.*")) == []


def test_mutable_ref_uses_new_snapshot_when_content_changes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    current_archive = _archive_bytes()
    downloads: list[str] = []

    def download(source: remote_data_roots.GitHubTreeSource) -> bytes:
        downloads.append(source.ref)
        return current_archive

    monkeypatch.setattr(remote_data_roots, "_download_archive", download)
    monkeypatch.setenv("LX_DTYPES_REMOTE_CACHE_ROOT", str(tmp_path))
    first = remote_data_roots.resolve_remote_data_root(
        _SOURCE_URL, module_name="remote_demo_module"
    )
    assert (
        remote_data_roots.resolve_remote_data_root(
            _SOURCE_URL, module_name="remote_demo_module"
        )
        == first
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "repo/demo-data/remote_demo_module/config.yaml",
            "name: remote_demo_module\nversion: 0.2.0\n",
        )
    current_archive = buffer.getvalue()
    second = remote_data_roots.resolve_remote_data_root(
        _SOURCE_URL, module_name="remote_demo_module"
    )
    assert first != second
    assert "0.2.0" in (second / "remote_demo_module/config.yaml").read_text()
    assert "0.1.0" in (first / "remote_demo_module/config.yaml").read_text()
    assert len(downloads) == 3


def test_commit_ref_reuses_cache_without_download(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LX_DTYPES_REMOTE_CACHE_ROOT", str(tmp_path))
    monkeypatch.setattr(
        remote_data_roots, "_download_archive", lambda source: _archive_bytes()
    )
    url = _SOURCE_URL.replace("/main/", "/" + "a" * 40 + "/")
    first = remote_data_roots.resolve_remote_data_root(
        url, module_name="remote_demo_module"
    )

    def unexpected_download(source: remote_data_roots.GitHubTreeSource) -> bytes:
        raise AssertionError("Immutable cache should be reused")

    monkeypatch.setattr(remote_data_roots, "_download_archive", unexpected_download)
    assert (
        remote_data_roots.resolve_remote_data_root(
            url, module_name="remote_demo_module"
        )
        == first
    )


def test_materialization_cleans_staging_when_atomic_write_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cache" / "cache-key"

    def failing_write(**kwargs: Any) -> Path:
        del kwargs
        raise OSError("injected write failure")

    monkeypatch.setattr(
        remote_data_roots,
        "_download_archive",
        lambda source: _archive_bytes(),
    )
    monkeypatch.setattr(
        remote_data_roots,
        "_filesystem_operations",
        lambda: remote_data_roots.FilesystemOperations(
            atomic_move_path=lambda **kwargs: kwargs["destination"],
            atomic_write_file=failing_write,
            ensure_directory=_ensure_directory,
            safe_rmtree=_remove_tree,
        ),
    )

    with pytest.raises(OSError, match="injected write failure"):
        remote_data_roots._materialize_archive(
            source_url=_SOURCE_URL,
            source=_SOURCE,
            destination=destination,
        )

    assert not destination.exists()
    assert list(destination.parent.glob(f".{destination.name}.*")) == []


def test_materialization_preserves_original_error_when_cleanup_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cache" / "cache-key"

    monkeypatch.setattr(
        remote_data_roots,
        "_download_archive",
        lambda source: _archive_bytes(),
    )
    monkeypatch.setattr(
        remote_data_roots,
        "_filesystem_operations",
        lambda: remote_data_roots.FilesystemOperations(
            atomic_move_path=lambda **kwargs: kwargs["destination"],
            atomic_write_file=lambda **kwargs: (_ for _ in ()).throw(
                OSError("original write failure")
            ),
            ensure_directory=_ensure_directory,
            safe_rmtree=lambda *args, **kwargs: (_ for _ in ()).throw(
                OSError("cleanup failure")
            ),
        ),
    )

    with pytest.raises(OSError, match="original write failure"):
        remote_data_roots._materialize_archive(
            source_url=_SOURCE_URL,
            source=_SOURCE,
            destination=destination,
        )


def test_cached_module_root_rejects_symlinked_module(tmp_path: Path) -> None:
    destination = tmp_path / "cache-key"
    real_module = tmp_path / "real-module"
    real_module.mkdir()
    (real_module / "config.yaml").write_text("name: remote_demo_module\n")
    module_parent = destination / "demo-data"
    module_parent.mkdir(parents=True)
    (module_parent / "remote_demo_module").symlink_to(
        real_module,
        target_is_directory=True,
    )

    assert (
        remote_data_roots._cached_module_root(
            destination=destination,
            source=_SOURCE,
        )
        is None
    )


def test_materialization_cleans_staging_after_publish_race_without_overwrite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cache" / "cache-key"

    def racing_move(*, source: Path, destination: Path, **kwargs: Any) -> Path:
        del source, kwargs
        destination.mkdir()
        (destination / "winner.txt").write_text("other process")
        raise FileExistsError(destination)

    monkeypatch.setattr(
        remote_data_roots,
        "_download_archive",
        lambda source: _archive_bytes(),
    )
    monkeypatch.setattr(
        remote_data_roots,
        "_filesystem_operations",
        lambda: remote_data_roots.FilesystemOperations(
            atomic_move_path=racing_move,
            atomic_write_file=_write_file,
            ensure_directory=_ensure_directory,
            safe_rmtree=_remove_tree,
        ),
    )

    with pytest.raises(FileExistsError):
        remote_data_roots._materialize_archive(
            source_url=_SOURCE_URL,
            source=_SOURCE,
            destination=destination,
        )

    assert (destination / "winner.txt").read_text() == "other process"
    assert list(destination.parent.glob(f".{destination.name}.*")) == []


def test_failed_refresh_preserves_existing_cache(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "cache-key"
    destination.mkdir()
    sentinel = destination / "incomplete.txt"
    sentinel.write_text("keep until a replacement is validated")
    monkeypatch.setattr(
        remote_data_roots, "_download_archive", lambda source: b"invalid zip"
    )
    with pytest.raises(remote_data_roots.RemoteDataRootError, match="valid ZIP"):
        remote_data_roots._materialize_archive(
            source_url=_SOURCE_URL,
            source=_SOURCE,
            destination=destination,
        )
    assert sentinel.read_text() == "keep until a replacement is validated"
    assert list(tmp_path.glob(".cache-key.*")) == []
