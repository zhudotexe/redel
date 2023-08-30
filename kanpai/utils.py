import uuid


def create_kani_id() -> str:
    """Create a unique identifier for a kani."""
    return str(uuid.uuid4())
