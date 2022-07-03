from pymoodle_jku.client.client import MoodleClient
from pymoodle_jku.client.download_manager import DownloadManager
from pymoodle_jku.utils.login import login
from pymoodle_jku.classes.course_data import UrlType, Url, CourseData, Section
from pymoodle_jku.classes.course import Course
from pymoodle_jku.classes.evaluation import Evaluation
from pymoodle_jku.classes.events import Event
from pymoodle_jku.scripts import basic, downloading, grades, timetable

import pymoodle_jku.utils.logging

# def main():
#     # try out some stuff
#     client = login()
#     method = ''
#     methodname = ''
#
#     resp = client.session.post(
#         f'https://moodle.jku.at/jku/lib/ajax/service.php?sesskey={client.sesskey}&info={method}',
#         json=[{"index": 0, "methodname": methodname, "args": {}}])
#
#     return 0
#

if __name__ == '__main__':
    pass
