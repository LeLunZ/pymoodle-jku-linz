from dataclasses import dataclass


@dataclass
class Event:
    """
    A Event object which represents the Moodle Calendar events.
    There are a lot of properties missing.
    """
    id: int
    name: str
    description: str
    modulename: str
    eventtype: str
    timestart: int
    timesort: int
    course_fullname: str
    course_id: int
    url: str
