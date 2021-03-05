from dataclasses import dataclass


@dataclass
class Event:
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
