import pytest

from ..Citation import Citation
from ..CitationDjango import CitationDjango


@pytest.fixture
def citation_fixture() -> Citation:
    """
    Create a sample Citation instance populated with typical bibliographic fields for use in tests.

    Returns:
        Citation: A Citation populated with name, citation_key, title, abstract, authors, publication_year, journal, doi, url, and keywords.
    """
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
    """
    Create a CitationDjango instance synchronized from the provided Citation fixture.

    Parameters:
        citation_fixture (Citation): A Citation test fixture whose `ddict` representation will be used to build the Django model.

    Returns:
        CitationDjango: A CitationDjango instance populated from `citation_fixture.ddict`.
    """
    citation_django = CitationDjango.sync_from_ddict(citation_fixture.ddict)

    return citation_django
