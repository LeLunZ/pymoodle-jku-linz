from dataclasses import dataclass

from pymoodle_jku.classes.course_data import UrlType, Url


@dataclass
class Evaluation:
    """
    A Evaluation for a Quiz or Assignment on Moodle.
    """
    name: str
    url: Url
    grade: str
    grade_range: str
