class TestCitation:
    def test_citation_no_key_titel_name(self):
        from lx_dtypes.models.shallow.citation import CitationShallow

        citation_data = {
            "title": "asd",
            "citation_key": "sdf",
            "created_at": "2024-01-01T00:00:00Z",
        }

        citation = CitationShallow(**citation_data)  # type:  ignore
        assert citation.name == "sdf"
