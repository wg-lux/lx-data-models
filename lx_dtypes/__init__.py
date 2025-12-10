from importlib import metadata

try:
    dist_name = (
        __package__.replace(  # pragma: no cover - only during local dev # type: ignore
            "_", "-"
        )
    )
    __version__ = metadata.version(dist_name)
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"
