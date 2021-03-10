from dataclasses import dataclass, field
from enum import Enum


class UrlType(Enum):
    """
    Represents the Ressource Type of links on Moodle.
    """
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
    Wiki = 11
    

@dataclass
class Url:
    """
    Represents a given URL on moodle.
    """
    link: str
    type: UrlType
    course: 'CourseData' = None


@dataclass
class Section:
    """
    Represents a Section of a moodle page.
    """
    text: str


@dataclass
class CourseData:
    """
    Represents the data from a course.
    """
    links: [Url] = field(default_factory=lambda: [])
    sections: [Section] = field(default_factory=lambda: [])
