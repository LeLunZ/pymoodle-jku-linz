from dataclasses import dataclass

from pymoodle_jku.classes.course_data import UrlType


@dataclass
class Evaluation:
    """
    A Evaluation for a Quiz or Assignment on Moodle.
    """
    name: str
    url: str
    type: UrlType
    grade: str
    grade_range: str
