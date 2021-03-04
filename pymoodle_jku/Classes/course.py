from dataclasses import dataclass
from typing import Union

from pymoodle_jku.Utils.moodle_html_parser import CoursePage


@dataclass
class Course:
    id: int
    fullname: str
    shortname: str
    idnumber: str
    summary: str
    summaryformat: int
    startdate: int
    enddate: int
    visible: bool
    fullnamedisplay: str
    viewurl: str
    courseimage: str
    progress: int
    hasprogress: bool
    isfavourite: bool
    hidden: bool
    showshortname: bool
    coursecategory: str
    course_page: Union[CoursePage, None] = None

    def __hash__(self):
        return hash(self.id)
