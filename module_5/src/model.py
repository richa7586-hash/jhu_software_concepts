"""Data model for applicant records."""


class ApplicantData:
    """Container for a single applicant record."""

    __slots__ = ("_data",)

    FIELDS = (
        "result_id",
        "university",
        "program",
        "masters_or_phd",
        "comments",
        "date_added",
        "url",
        "applicant_status",
        "decision_date",
        "semester_year_start",
        "citizenship",
        "gpa",
        "gre",
        "gre_v",
        "gre_aw",
        "status",
    )

    def __init__(self):
        self._data = {field: None for field in self.FIELDS}

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"{type(self).__name__} has no attribute {name!r}")

    def __setattr__(self, name, value):
        if name == "_data":
            object.__setattr__(self, name, value)
            return
        data = object.__getattribute__(self, "_data")
        if name in data:
            data[name] = value
            return
        object.__setattr__(self, name, value)

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return dict(self._data)
