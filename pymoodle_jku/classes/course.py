from dataclasses import dataclass
from typing import Union

from pymoodle_jku.client.html_parser import CoursePage


def parse_course_name(fullname):
    try:
        return fullname.split(',')[1].strip()
    except IndexError:
        return fullname


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

    def _cmp(self, other):
        if (self.enddate is None or self.enddate == 0) and (other.enddate is None or other.enddate == 0):
            return 0
        elif (other.enddate is None or other.enddate == 0):
            return -1
        elif (self.enddate is None or self.enddate == 0):
            return 1
        return self.enddate - other.enddate

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __eq__(self, other):
        return self._cmp(other) == 0

    def __ne__(self, other):
        return self._cmp(other) != 0

    def __ge__(self, other):
        return self._cmp(other) >= 0

    def __gt__(self, other):
        return self._cmp(other) > 0
