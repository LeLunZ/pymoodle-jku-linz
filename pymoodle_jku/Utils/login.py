import logging

from pymoodle_jku.Client.client import MoodleClient, DownloadManager

logger = logging.getLogger(__name__)


def debug(msg):
    logger.debug(f'UniJob: {msg}')


def login(username=None, password=None):
    client = MoodleClient()
    auth = False
    while not auth:
        try:
            if username is None:
                username = input('username: ')
            if password is None:
                password = input('password: ')
            auth = client.login(username, password)
        except:
            print('Login failed, trying again...')
            debug('Login failed, trying again...')
    return client

