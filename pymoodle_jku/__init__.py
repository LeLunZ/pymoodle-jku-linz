from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Client.download_manager import DownloadManager
from pymoodle_jku.Utils.login import login
from pymoodle_jku.Classes.course_data import UrlType, Url, CourseData, Section
from pymoodle_jku.Classes.course import Course
from pymoodle_jku.Classes.evaluation import Evaluation
from pymoodle_jku.Classes.events import Event

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
