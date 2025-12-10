from datetime import date

from lx_dtypes.models.base_models.person import Person


class TestPersonModel:
    def test_person_model_with_dob(self, sample_person: Person):
        person = sample_person
        assert person.first_name == "Alice"
        assert person.last_name == "Johnson"
        assert person.dob == date(1985, 7, 20)
        assert person.email is None
        assert person.gender == "female"
        assert person.uuid is not None

    def test_person_model_no_dob_no_gender(
        self, sample_person_no_dob_no_gender: Person
    ):
        person = sample_person_no_dob_no_gender
        assert person.first_name == "John"
        assert person.last_name == "Doe"
        assert person.dob is None
        assert person.email is None
