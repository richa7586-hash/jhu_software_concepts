import builtins
import json
import runpy
import time

import pytest

import config
import clean
import load_data
import scrape
from model import ApplicantData


def _time_sequence(values):
    # Return a time.time stub that yields provided values in order.
    iterator = iter(values)
    last_value = values[-1]

    def _fake_time():
        # Advance through the predefined time values.
        nonlocal last_value
        try:
            last_value = next(iterator)
        except StopIteration:
            return last_value
        return last_value

    return _fake_time


def _list_page_html(include_badge_row=True):
    # Build minimal list page HTML with a single result row.
    badge_row = ""
    if include_badge_row:
        badge_row = """
        <tr>
          <td colspan="3">
            <div class="tw-inline-flex md:tw-hidden">Accepted on 01/02/2024 Fall 2026 GPA 3.8</div>
            <div class="tw-inline-flex">Fall 2026</div>
            <div class="tw-inline-flex">International</div>
            <div class="tw-inline-flex">GPA 3.9</div>
          </td>
        </tr>
        """
    return f"""
    <html>
      <body>
        <table>
          <tr>
            <td><div class="tw-font-medium">Test University</div></td>
            <td>
              <div class="tw-text-gray-900">
                <span>Computer Science</span>
                <span>Masters</span>
              </div>
            </td>
            <td>January 1, 2024</td>
            <td>Other</td>
            <td><a href="/result/123">See More</a></td>
          </tr>
          {badge_row}
        </table>
      </body>
    </html>
    """


@pytest.mark.db
def test_fetch_page_success(monkeypatch):
    # fetch_page should return decoded HTML when the request succeeds.
    class DummyResponse:
        def __init__(self):
            # Provide bytes to decode into a string.
            self.data = b"<html>ok</html>"

    monkeypatch.setattr(scrape, "request", lambda _method, _url: DummyResponse())

    scraper = scrape.GradCafeScraper()
    assert scraper.fetch_page("http://example.com") == "<html>ok</html>"


@pytest.mark.db
def test_fetch_page_handles_exception(monkeypatch):
    # fetch_page should return None when the request raises.
    def _raise(*_args, **_kwargs):
        # Simulate a network error.
        raise RuntimeError("boom")

    monkeypatch.setattr(scrape, "request", _raise)

    scraper = scrape.GradCafeScraper()
    assert scraper.fetch_page("http://example.com") is None


@pytest.mark.db
def test_parse_list_page_no_table():
    # parse_list_page should return an empty list when no table exists.
    scraper = scrape.GradCafeScraper()
    assert scraper.parse_list_page("<html></html>") == []


@pytest.mark.db
def test_parse_list_page_parses_row_and_badges():
    # parse_list_page should populate applicant fields from rows and badges.
    scraper = scrape.GradCafeScraper()
    applicants = scraper.parse_list_page(_list_page_html())

    assert len(applicants) == 1
    applicant = applicants[0]
    assert applicant.result_id == "123"
    assert applicant.url.endswith("/result/123")
    assert applicant.university == "Test University"
    assert applicant.program == "Computer Science, Test University"
    assert applicant.masters_or_phd == "Masters"
    assert applicant.date_added == "January 1, 2024"
    assert applicant.status == "Accepted"
    assert applicant.decision_date == "01/02/2024"
    assert applicant.semester_year_start == "Fall 2026"
    assert applicant.citizenship == "International"
    assert applicant.gpa == "3.9"


@pytest.mark.db
def test_parse_list_page_handles_basic_info_error(monkeypatch, capsys):
    # Basic info parsing errors should be caught and logged.
    class ExplodingApplicant:
        def __init__(self):
            # Allow required fields to be assigned outside the try block.
            self.result_id = None
            self.url = None

        def __setattr__(self, name, value):
            # Trigger an exception when setting the university.
            if name == "university":
                raise ValueError("boom")
            object.__setattr__(self, name, value)

    monkeypatch.setattr(scrape, "ApplicantData", ExplodingApplicant)

    scraper = scrape.GradCafeScraper()
    applicants = scraper.parse_list_page(_list_page_html(include_badge_row=False))

    captured = capsys.readouterr()
    assert "Error parsing basic info" in captured.out
    assert len(applicants) == 1


@pytest.mark.db
def test_parse_list_page_handles_badge_error(monkeypatch, capsys):
    # Badge parsing errors should be caught and logged.
    def _raise(*_args, **_kwargs):
        # Force the badge parsing path to fail.
        raise RuntimeError("boom")

    monkeypatch.setattr(scrape.GradCafeScraper, "_parse_status_info", _raise)

    scraper = scrape.GradCafeScraper()
    applicants = scraper.parse_list_page(_list_page_html())

    captured = capsys.readouterr()
    assert "Error parsing badges" in captured.out
    assert len(applicants) == 1


@pytest.mark.db
def test_parse_status_info_sets_american_fields():
    # _parse_status_info should set status, decision date, and American citizenship.
    scraper = scrape.GradCafeScraper()
    applicant = ApplicantData()

    scraper._parse_status_info("Accepted on 01/02/2024 Fall 2026 American GPA 3.7", applicant)

    assert applicant.status == "Accepted"
    assert applicant.decision_date == "01/02/2024"
    assert applicant.semester_year_start == "Fall 2026"
    assert applicant.citizenship == "American"
    assert applicant.gpa == "3.7"


@pytest.mark.db
def test_parse_status_info_sets_international_fields():
    # _parse_status_info should support International citizenship text.
    scraper = scrape.GradCafeScraper()
    applicant = ApplicantData()

    scraper._parse_status_info("Rejected on 02/03/2024 Spring 2025 International", applicant)

    assert applicant.status == "Rejected"
    assert applicant.decision_date == "02/03/2024"
    assert applicant.semester_year_start == "Spring 2025"
    assert applicant.citizenship == "International"


@pytest.mark.db
def test_parse_detail_page_parses_fields():
    # parse_detail_page should populate applicant details from the HTML.
    html = """
    <html>
      <body>
        <dt>Notes</dt><dd>These are notes.</dd>
        <ul>
          <li class="tw-flex">
            <span class="tw-font-medium">GRE General</span>
            <span class="tw-text-gray-400">320</span>
          </li>
          <li class="tw-flex">
            <span class="tw-font-medium">GRE Verbal</span>
            <span class="tw-text-gray-400">N/A</span>
          </li>
          <li class="tw-flex">
            <span class="tw-font-medium">GRE Verbal</span>
            <span class="tw-text-gray-400">160</span>
          </li>
          <li class="tw-flex">
            <span class="tw-font-medium">Analytical Writing</span>
            <span class="tw-text-gray-400">4.5</span>
          </li>
          <li class="tw-flex">
            <span class="tw-font-medium">Undergrad GPA</span>
            <span class="tw-text-gray-400">3.9</span>
          </li>
          <li class="tw-flex">
            <span class="tw-font-medium">GRE General</span>
            <span class="tw-text-gray-400">0</span>
          </li>
        </ul>
        <div>Notification on: 1/2/2024</div>
        <dt>Degree's Country of Origin</dt><dd>Canada</dd>
      </body>
    </html>
    """
    scraper = scrape.GradCafeScraper()
    applicant = ApplicantData()
    applicant.result_id = "123"

    scraper.parse_detail_page(html, applicant)

    assert applicant.comments == "These are notes."
    assert applicant.gre == "320.0"
    assert applicant.gre_v == "160.0"
    assert applicant.gre_aw == "4.5"
    assert applicant.gpa == "3.9"
    assert applicant.decision_date == "1/2/2024"
    assert applicant.citizenship == "Canada"


@pytest.mark.db
def test_parse_detail_page_skips_missing_spans():
    # Missing label/value spans should be skipped without errors.
    html = """
    <html>
      <body>
        <ul>
          <li class="tw-flex">
            <span class="tw-font-medium">GRE General</span>
          </li>
        </ul>
      </body>
    </html>
    """
    scraper = scrape.GradCafeScraper()
    applicant = ApplicantData()

    scraper.parse_detail_page(html, applicant)

    assert applicant.gre is None


@pytest.mark.db
def test_parse_detail_page_handles_float_value_error(monkeypatch):
    # ValueError from float conversion should be handled gracefully.
    html = """
    <html>
      <body>
        <ul>
          <li class="tw-flex">
            <span class="tw-font-medium">GRE General</span>
            <span class="tw-text-gray-400">123</span>
          </li>
        </ul>
      </body>
    </html>
    """
    real_float = builtins.float

    def _fail_float(value):
        # Raise only for the targeted test value.
        if value == "123":
            raise ValueError("boom")
        return real_float(value)

    monkeypatch.setattr(builtins, "float", _fail_float)

    scraper = scrape.GradCafeScraper()
    applicant = ApplicantData()

    scraper.parse_detail_page(html, applicant)

    assert applicant.gre is None


@pytest.mark.db
def test_parse_detail_page_handles_exception(monkeypatch, capsys):
    # parse_detail_page should log errors encountered while parsing.
    class ExplodingApplicant:
        def __init__(self):
            # Preserve result_id for error logging.
            self.result_id = "123"

        def __setattr__(self, name, value):
            # Trigger an error when setting comments.
            if name == "comments":
                raise ValueError("boom")
            object.__setattr__(self, name, value)

    html = "<dt>Notes</dt><dd>These are notes.</dd>"
    scraper = scrape.GradCafeScraper()

    scraper.parse_detail_page(html, ExplodingApplicant())

    captured = capsys.readouterr()
    assert "Error parsing detail page" in captured.out


@pytest.mark.db
def test_save_data_writes_new_file(tmp_path):
    # save_data should create a JSON list when the file does not exist.
    scraper = scrape.GradCafeScraper()
    scraper.data_file = str(tmp_path / "data.json")
    applicant = ApplicantData()

    scraper.save_data([applicant])

    data = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
    assert len(data) == 1
    assert "program" in data[0]


@pytest.mark.db
def test_save_data_appends_existing_records(tmp_path):
    # save_data should append to existing JSON data.
    data_path = tmp_path / "data.json"
    data_path.write_text('[{"program": "Existing"}]', encoding="utf-8")

    scraper = scrape.GradCafeScraper()
    scraper.data_file = str(data_path)
    applicant = ApplicantData()

    scraper.save_data([applicant])

    data = json.loads(data_path.read_text(encoding="utf-8"))
    assert len(data) == 2


@pytest.mark.db
def test_save_data_handles_error(tmp_path, capsys):
    # save_data should log errors when file IO fails.
    scraper = scrape.GradCafeScraper()
    scraper.data_file = str(tmp_path)

    scraper.save_data([])

    captured = capsys.readouterr()
    assert "Error saving data" in captured.out


@pytest.mark.db
def test_scrape_page_handles_fetch_failure(monkeypatch):
    # scrape_page should return an empty list when the list page fails to load.
    scraper = scrape.GradCafeScraper()
    monkeypatch.setattr(scraper, "fetch_page", lambda _url: None)

    assert scraper.scrape_page(1) == []


@pytest.mark.db
def test_scrape_page_returns_empty_when_no_results(monkeypatch):
    # scrape_page should return an empty list when no applicants are found.
    scraper = scrape.GradCafeScraper()
    monkeypatch.setattr(scraper, "fetch_page", lambda _url: "<html></html>")

    assert scraper.scrape_page(1) == []


@pytest.mark.db
def test_scrape_page_handles_detail_success_and_failure(monkeypatch):
    # scrape_page should parse details for success and skip failures.
    scraper = scrape.GradCafeScraper()
    applicant_one = ApplicantData()
    applicant_one.result_id = "1"
    applicant_one.url = "http://detail/1"
    applicant_two = ApplicantData()
    applicant_two.result_id = "2"
    applicant_two.url = "http://detail/2"

    calls = {"count": 0, "parsed": []}

    def _fake_fetch(url):
        # Return list HTML first, then detail HTML, then None.
        calls["count"] += 1
        if calls["count"] == 1:
            return "<html>list</html>"
        if calls["count"] == 2:
            return "<html>detail</html>"
        return None

    def _fake_parse_detail(_html, applicant):
        # Track which applicant was parsed.
        calls["parsed"].append(applicant.result_id)

    monkeypatch.setattr(scraper, "fetch_page", _fake_fetch)
    monkeypatch.setattr(scraper, "parse_list_page", lambda _html: [applicant_one, applicant_two])
    monkeypatch.setattr(scraper, "parse_detail_page", _fake_parse_detail)

    result = scraper.scrape_page(1)

    assert len(result) == 2
    assert calls["parsed"] == ["1"]


@pytest.mark.db
def test_pull_data_handles_empty_pages(monkeypatch, tmp_path):
    # pull_data should advance pages and still run clean/load steps.
    scraper = scrape.GradCafeScraper()
    scraper.data_file = str(tmp_path / "data.json")

    clean_called = {"value": False}
    load_called = {"value": False}

    monkeypatch.setattr(scraper, "scrape_page", lambda _page: [])
    monkeypatch.setattr(scrape, "clean_data", lambda **_kwargs: clean_called.__setitem__("value", True))
    monkeypatch.setattr(scrape.load_data, "main", lambda: load_called.__setitem__("value", True))
    monkeypatch.setattr(time, "time", _time_sequence([0.0, 0.0, 2.0, 2.0]))

    scraper.pull_data(max_seconds=1)

    assert clean_called["value"] is True
    assert load_called["value"] is True
    assert json.loads((tmp_path / "data.json").read_text(encoding="utf-8")) == []


@pytest.mark.db
def test_pull_data_handles_results(monkeypatch, tmp_path):
    # pull_data should save results and call downstream steps.
    scraper = scrape.GradCafeScraper()
    scraper.data_file = str(tmp_path / "data.json")

    applicant = ApplicantData()
    applicant.url = "http://example.com/1"
    clean_called = {"value": False}
    load_called = {"value": False}
    saved = {"rows": 0}

    monkeypatch.setattr(scraper, "scrape_page", lambda _page: [applicant])
    monkeypatch.setattr(scraper, "save_data", lambda rows: saved.__setitem__("rows", len(rows)))
    monkeypatch.setattr(scrape, "clean_data", lambda **_kwargs: clean_called.__setitem__("value", True))
    monkeypatch.setattr(scrape.load_data, "main", lambda: load_called.__setitem__("value", True))
    monkeypatch.setattr(time, "time", _time_sequence([0.0, 0.0, 2.0, 2.0]))

    scraper.pull_data(max_seconds=1)

    assert saved["rows"] == 1
    assert clean_called["value"] is True
    assert load_called["value"] is True


@pytest.mark.db
def test_scrape_module_main_uses_entrypoint(monkeypatch, tmp_path):
    # __main__ should execute quickly with patched dependencies.
    data_path = tmp_path / "data.json"

    monkeypatch.setattr(config, "DATA_FILE", str(data_path))
    monkeypatch.setattr(time, "time", _time_sequence([0.0, 11.0, 11.0]))
    monkeypatch.setattr(clean, "clean_data", lambda **_kwargs: None)
    monkeypatch.setattr(load_data, "main", lambda: None)

    runpy.run_module("scrape", run_name="__main__")

    assert json.loads(data_path.read_text(encoding="utf-8")) == []
