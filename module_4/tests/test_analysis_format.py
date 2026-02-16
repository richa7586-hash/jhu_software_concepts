from decimal import Decimal
import re

import pytest
from bs4 import BeautifulSoup


@pytest.mark.analysis
def test_analysis_page_includes_answer_labels(analysis_client):
    # Verify the analysis page renders Answer labels for results.
    response = analysis_client().get("/analysis")

    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    assert "Answer:" in soup.get_text()


@pytest.mark.analysis
def test_analysis_page_formats_percentages_with_two_decimals(analysis_client):
    # Verify percentage answers render with two decimal places.
    client = analysis_client(
        rows=[(Decimal("12.3"),)],
        question="What percent of entries are international?",
    )
    response = client.get("/analysis")
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    assert re.search(r"\d+\.\d{2}%", soup.get_text())


@pytest.mark.analysis
def test_analysis_page_handles_empty_results(analysis_client):
    # Ensure empty query results render the fallback message.
    client = analysis_client(rows=[])
    response = client.get("/analysis")
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    assert "No data returned." in soup.get_text()
