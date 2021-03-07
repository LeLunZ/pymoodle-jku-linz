from dataclasses import dataclass
from typing import Union

from pymoodle_jku.Client.html_parser import CoursePage


def parse_course_name(fullname):
    return fullname.split(',')[1].strip()


@dataclass
class Course:
    """
    Represents the Course object which is loaded from Moodle.
    """
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

    def parse_name(self):
        return parse_course_name(self.fullname)

    def __hash__(self):
        return hash(self.id)
