from pathlib import Path
from typing import Callable

from pytest import FixtureRequest, fixture

from lx_dtypes.models.base_models.log import Log
from lx_dtypes.utils.logging import LogLevel, LogScope, ScopedLogWriter, get_logger


@fixture
def log_writer(logger: ScopedLogWriter, request: FixtureRequest) -> Callable[..., Log]:
    nodeid = request.node.nodeid  # type: ignore[attr-defined]
    request_cls = request.cls  # type: ignore[attr-defined]
    if request_cls is not None:
        test_class = request_cls.__name__  # type: ignore[attr-defined]
        assert isinstance(test_class, str)
    else:
        test_class = None
    test_name = request.function.__name__

    if not isinstance(nodeid, str):  # pytest guarantees str but mypy does not
        raise TypeError("pytest nodeid must be a string")

    base_context: dict[str, str] = {
        "test": nodeid,
        "test_name": test_name,
    }

    def emit(
        message: str,
        *,
        level: LogLevel = LogLevel.INFO,
        context: dict[str, str] | None = None,
    ) -> Log:
        merged = {**base_context, **(context or {})}
        return logger.log(message, level=level, context=merged)

    return emit


@fixture(scope="session")
def logger(log_dir: Path) -> ScopedLogWriter:
    scoped_logger = get_logger(
        scope=LogScope.TESTS,
        root_dir=log_dir,
        output_format="yaml",
    )
    return scoped_logger
