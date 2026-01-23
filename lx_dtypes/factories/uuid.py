import uuid


def uuid_factory() -> uuid.UUID:
    """
    Generate a new random UUID.

    Returns:
        uuid.UUID: The generated UUID.
    """

    return uuid.uuid4()


def str_uuid_factory() -> str:
    """
    Generates a new UUID and returns its canonical string representation.

    Returns:
        uuid_str (str): UUID in standard 36-character canonical form (hexadecimal, 8-4-4-4-12).
    """

    return str(uuid_factory())
