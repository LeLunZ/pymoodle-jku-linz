from logging.config import dictConfig
from pathlib import Path

from pymoodle_jku.client.client import MoodleClient
from pymoodle_jku.client.download_manager import DownloadManager
from pymoodle_jku.utils.login import login
from pymoodle_jku.classes.course_data import UrlType, Url, CourseData, Section
from pymoodle_jku.classes.course import Course
from pymoodle_jku.classes.evaluation import Evaluation
from pymoodle_jku.classes.events import Event

dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'default': {
        'formatter': 'default',
        'level': 'DEBUG',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': str(Path.home() / '.pymoodle.log'),
        'maxBytes': 20000000
    }},
    'loggers': {
        'pymoodle_jku': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        '__main__': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        '': {
            'handlers': ['default'],
            'level': 'ERROR',
            'propagate': True
        },
    }
})
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
