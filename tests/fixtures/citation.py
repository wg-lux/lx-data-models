from pytest import fixture

from lx_dtypes.models.core.citation import Citation


@fixture
def sample_citation() -> Citation:
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
