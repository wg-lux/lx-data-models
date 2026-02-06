from pathlib import Path

from lx_dtypes.models.ledger.p_video import (
    PatientVideoFile,
    PatientVideoFileDataDict,
)


class TestVideoBaseModel:
    def test_raw_video_fixture(self, raw_video_file_path: Path) -> None:
        assert raw_video_file_path.exists()
        assert raw_video_file_path.is_file()
        assert raw_video_file_path.suffix == ".mp4"

    def test_video_base_model_fixture(
        self,
        patient_video_file_fixture: "PatientVideoFile",
        patient_video_file_data_dict_fixture: PatientVideoFileDataDict,
    ) -> None:
        pydantic_path = patient_video_file_fixture.file
        ddict_path = patient_video_file_data_dict_fixture["fnd"].get("file", None)
        assert ddict_path is not None
        assert pydantic_path == Path(ddict_path)

        # Create Segment
        segment = patient_video_file_fixture.create_segment(
            start_frame_number=100,
            end_frame_number=150,
            label="test_label",
            labelset="test_labelset",
        )
        assert str(segment.uuid) in patient_video_file_fixture.patient_video_segments
        assert (
            patient_video_file_fixture.patient_video_segments[str(segment.uuid)]
            == segment
        )

        # Update Segment
        updated_segment = patient_video_file_fixture.update_segment(
            segment_uuid=str(segment.uuid),
            start_frame_number=110,
            end_frame_number=160,
            label="updated_test_label",
            labelset="updated_test_labelset",
        )
        assert updated_segment.start_frame_number == 110
        assert updated_segment.end_frame_number == 160
        assert updated_segment.label == "updated_test_label"
        assert updated_segment.labelset == "updated_test_labelset"
        assert (
            patient_video_file_fixture.patient_video_segments[str(segment.uuid)]
            == updated_segment
        )

        # validate ddict conversion
        ddict = patient_video_file_fixture.ddict
        new_obj = patient_video_file_fixture.model_validate(ddict)
        new_ddict = new_obj.ddict

        # test validation function
        assert patient_video_file_fixture.validate_ddict(new_obj.model_dump()) is True

        assert ddict == new_ddict

        patient_video_file_fixture.to_yaml(
            Path(__file__).parent / "p_video_fixture.yaml"
        )
