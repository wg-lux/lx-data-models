import json
from pathlib import Path

import yaml

from lx_dtypes.models.base_models.log import LogLevel, LogScope
from lx_dtypes.utils.logging import ScopedLogWriter, get_logger


def test_scoped_logger_writes_yaml_per_test(tmp_path: Path):
    logger = ScopedLogWriter(LogScope.TESTS, root_dir=tmp_path, output_format="yaml")

    context = {
        "test": "tests/logs/test_scoped_logger.py::TestScopedLogger::test_scoped_logger_writes_yaml_per_test",
        "case": "A",
    }
    entry = logger.log("hello world", level=LogLevel.DEBUG, context=context)

    expected_dir = tmp_path / "tests" / "TestScopedLogger"
    expected_file = expected_dir / f"{entry.timestamp.date().isoformat()}_test_scoped_logger_writes_yaml_per_test.log.yaml"
    assert expected_file.exists()

    docs = list(yaml.safe_load_all(expected_file.read_text(encoding="utf-8")))
    payload = docs[-1]
    assert payload["message"] == "hello world"
    assert payload["level"] == LogLevel.DEBUG.value
    assert payload["scope"] == LogScope.TESTS.value
    assert payload["context"] == context


def test_get_logger_default_level(tmp_path: Path):
    logger = get_logger(LogScope.SCRIPTS, root_dir=tmp_path)

    entry = logger.log("script executed")

    log_path = tmp_path / "scripts" / f"{entry.timestamp.date().isoformat()}.log.jsonl"
    assert log_path.exists()

    payload = json.loads(log_path.read_text().strip().splitlines()[-1])
    assert payload["level"] == LogLevel.INFO.value
    assert payload["message"] == "script executed"


def test_get_logger_default_path(tmp_path: Path):
    logger = get_logger(LogScope.TESTS, root_dir=tmp_path)

    entry = logger.log("default path log")

    log_path = tmp_path / "tests" / f"{entry.timestamp.date().isoformat()}.log.jsonl"
    assert log_path.exists()

    payload = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
    assert payload["message"] == "default path log"
