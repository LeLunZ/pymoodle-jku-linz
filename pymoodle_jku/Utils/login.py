import logging
from pathlib import Path

import keyring

from pymoodle_jku.Client.client import MoodleClient

logger = logging.getLogger(__name__)


def debug(msg):
    logger.debug(f'UniJob: {msg}')


def login(username=None, password=None, save_password_query=True) -> MoodleClient:
    client = MoodleClient()
    pymoodle_conf = Path.home() / '.pymoodle'
    if pymoodle_conf.is_file():
        username = pymoodle_conf.read_text().strip()
        password = keyring.get_password('pymoodle-jku', username)
    auth = False
    while not auth:
        try:
            if username is None:
                username = input('username: ')
            if password is None:
                password = input('password: ')
            if save_password_query and not pymoodle_conf.is_file():
                save_password = input('do you want to store your password in your local keyring: (y/n)').strip().lower()
                if save_password == 'y':
                    pymoodle_conf.write_text(username)
                    keyring.set_password('pymoodle-jku', username, password)
            auth = client.login(username, password)
        except:
            print('Login failed, trying again...')
            debug('Login failed, trying again...')
    return client
