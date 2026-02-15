import pytest

from model import ApplicantData


@pytest.mark.db
def test_applicant_data_defaults_are_none():
    # New instances should start with all expected fields set to None.
    applicant = ApplicantData()
    assert applicant.result_id is None
    assert applicant.university is None
    assert applicant.program is None
    assert applicant.masters_or_phd is None
    assert applicant.comments is None
    assert applicant.date_added is None
    assert applicant.url is None
    assert applicant.applicant_status is None
    assert applicant.decision_date is None
    assert applicant.semester_year_start is None
    assert applicant.citizenship is None
    assert applicant.gpa is None
    assert applicant.gre is None
    assert applicant.gre_v is None
    assert applicant.gre_aw is None


@pytest.mark.db
def test_applicant_data_to_dict_exposes_all_fields():
    # to_dict should return a mapping of field names to values.
    applicant = ApplicantData()
    data = applicant.to_dict()
    assert data["result_id"] is None
    assert data["university"] is None
    assert data["program"] is None
    assert data["masters_or_phd"] is None
    assert data["comments"] is None
    assert data["date_added"] is None
    assert data["url"] is None
    assert data["applicant_status"] is None
    assert data["decision_date"] is None
    assert data["semester_year_start"] is None
    assert data["citizenship"] is None
    assert data["gpa"] is None
    assert data["gre"] is None
    assert data["gre_v"] is None
    assert data["gre_aw"] is None
