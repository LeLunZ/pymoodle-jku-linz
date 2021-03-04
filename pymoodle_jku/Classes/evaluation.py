from dataclasses import dataclass

from pymoodle_jku.Classes.course_data import UrlType


@dataclass
class Evaluation:
    name: str
    url: str
    type: UrlType
    grade: str
    grade_range: str
