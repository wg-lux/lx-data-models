import uuid


def uuid_factory() -> uuid.UUID:
    """Generate a UUID (uses uuid.uuid4)"""

    return uuid.uuid4()


def str_uuid_factory() -> str:
    """calls uuid_factory and turns result into str."""

    return str(uuid_factory())
