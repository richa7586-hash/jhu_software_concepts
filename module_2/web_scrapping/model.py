class ApplicantData:
    def __init__(self):
        self.result_id = ""
        self.url = ""
        self.university = None
        self.program = None
        self.degree_type = None
        self.date_added = None
        self.status = None
        self.status_date = None
        self.semester = None
        self.year = None
        self.student_type = None
        self.gpa = None
        self.gre_score = ""
        self.gre_v_score = ""
        self.gre_aw_score = ""
        self.comments = ""

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return self.__dict__
