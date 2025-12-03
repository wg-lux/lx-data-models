from datetime import datetime, timezone

from pytest import fixture

from lx_dtypes.models.base_models.examination import BaseExamination

start_dt = datetime(2023, 1, 1, 9, 0, tzinfo=timezone.utc)
end_dt = datetime(2023, 1, 1, 17, 0, tzinfo=timezone.utc)
examination_date = start_dt.date()


@fixture(scope="function")
def base_examination():
    return BaseExamination(
        name="Sample Examination",
        date=examination_date,
        start_time=start_dt,
        end_time=end_dt,
        description="This is a sample examination with start / end-times and date.",
    )


class TestBaseExaminationModel:
    def test_base_examination_fixture(self, base_examination: BaseExamination):
        assert base_examination.name == "Sample Examination"
        assert base_examination.date == examination_date
        assert base_examination.start_time == start_dt
        assert base_examination.end_time == end_dt
        assert base_examination.description == "This is a sample examination with start / end-times and date."
