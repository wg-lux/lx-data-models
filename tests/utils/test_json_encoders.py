from pathlib import Path

from lx_dtypes.utils.json_encoders import serialize_path


class TestJsonEncoders:
    def test_serialize_path_with_valid_path(self):
        path = Path("/some/test/path")
        serialized = serialize_path(path)
        assert serialized == "/some/test/path"

    def test_serialize_path_with_none(self):
        path = None
        serialized = serialize_path(path)
        assert serialized is None
