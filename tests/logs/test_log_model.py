class TestLogModel:
    def test_log_model_timestamp(self):
        from datetime import datetime, timezone

        from lx_dtypes.models.base_models.log import Log, LogScope

        log_entry = Log(message="testing log", scope=LogScope.TESTS)
        assert isinstance(log_entry.timestamp, datetime)
        assert log_entry.timestamp.tzinfo == timezone.utc
