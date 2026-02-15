from decimal import Decimal

import pytest


@pytest.mark.analysis
def test_analysis_page_includes_answer_labels(analysis_client):
    # Verify the analysis page renders Answer labels for results.
    response = analysis_client().get("/analysis")

    html = response.get_data(as_text=True)
    assert "Answer:" in html


@pytest.mark.analysis
def test_analysis_page_formats_percentages_with_two_decimals(analysis_client):
    # Verify percentage answers render with two decimal places.
    client = analysis_client(
        rows=[(Decimal("12.3"),)],
        question="What percent of entries are international?",
    )
    response = client.get("/analysis")
    html = response.get_data(as_text=True)

    assert "12.30" in html
