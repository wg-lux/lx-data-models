from typing import Callable

from lx_dtypes.utils.logging import Log


class TestLogWriter:
    def test_log_writer_functionality(self, log_writer: Callable[..., Log]):
        log_writer("Test log message")
