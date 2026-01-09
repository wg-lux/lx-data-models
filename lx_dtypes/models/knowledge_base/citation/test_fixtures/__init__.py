import pytest

from ..Citation import Citation
from ..CitationDjango import CitationDjango


@pytest.fixture
def citation_fixture() -> Citation:
    return Citation(
        name="Sample Citation",
        citation_key="Doe2024Sample",
        title="A Sample Citation for Testing",
        abstract="This is a sample abstract for the citation used in testing.",
        authors=["John Doe", "Jane Smith"],
        publication_year=2024,
        journal="Journal of Testing",
        doi="10.1234/sample.doi",
        url="https://example.com/sample-citation",
        keywords=["testing", "sample", "citation"],
    )


@pytest.fixture
def django_citation_fixture(citation_fixture: Citation) -> CitationDjango:
    citation_django = CitationDjango.sync_from_ddict(citation_fixture.ddict)

    return citation_django
