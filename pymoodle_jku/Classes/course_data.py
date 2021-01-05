from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from pymoodle_jku.Classes.course import Course


class UrlType(Enum):
    Streamurl = 0  # stream
    Resource = 1
    Assign = 2  # assignment
    Url = 3
    Folder = 4
    Zoom = 5
    Page = 6
    Quiz = 7
    Choice = 8
    Grouptool = 9
    Forum = 10
    Checkmark = 11


@dataclass
class Url:
    link: str
    type: UrlType
    course: 'CourseData' = None


@dataclass
class Section:
    text: str


@dataclass
class CourseData:
    course: Course = None
    links: [Url] = field(default_factory=lambda: [])
    sections: [Section] = field(default_factory=lambda: [])
