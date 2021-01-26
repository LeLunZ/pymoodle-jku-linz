import logging

from pymoodle_jku.Client.client import MoodleClient, DownloadManager

logger = logging.getLogger(__name__)


def get_timetable():
    client = MoodleClient()
    auth = False
    while not auth:
        try:
            auth = client.login(input('username: '), input('password: '))
        except:
            pass
    timetable = client.calendar()
    print(timetable)


if __name__ == "__main__":
    print(get_timetable())
