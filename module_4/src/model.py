class ApplicantData:
    def __init__(self):
        self.result_id = None
        self.university = None
        self.program = None
        self.masters_or_phd = None
        self.comments = None
        self.date_added = None
        self.url = None
        self.applicant_status = None
        self.decision_date = None
        self.semester_year_start = None
        self.citizenship = None
        self.gpa = None
        self.gre = None
        self.gre_v = None
        self.gre_aw = None

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return self.__dict__
