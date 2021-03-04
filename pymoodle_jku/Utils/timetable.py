import logging

from pymoodle_jku.Utils.login import login

logger = logging.getLogger(__name__)


def get_timetable():
    client = login()
    timetable = client.calendar()
    print(timetable)


if __name__ == "__main__":
    print(get_timetable())
