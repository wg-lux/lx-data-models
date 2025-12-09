from pathlib import Path


def serialize_path(path: Path | None) -> str | None:
    """Serialize a Path object to its POSIX string representation.

    Args:
        path (Path | None): The Path object to serialize.

    Returns:
        str | None: The POSIX string representation of the path, or None if the input is None.
    """
    if path is not None:
        return path.as_posix()
    return None
