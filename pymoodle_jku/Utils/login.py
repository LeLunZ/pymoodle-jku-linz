import logging
from concurrent.futures.thread import ThreadPoolExecutor
from getpass import getpass
from pathlib import Path
from typing import Optional

import keyring

from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Utils.config import config, write_config
from pymoodle_jku.Utils.printing import yn_question

logger = logging.getLogger(__name__)


def debug(msg):
    logger.debug(f'UniJob: {msg}')


def login(credentials, threads: int = None) -> Optional[MoodleClient]:
    """
    Tries to Login the user multiple times.

    :param credentials: Tuple[str, str] with (username, password).
    :param threads: the amount of threads to use for crawling.
    :return: A Moodle Client if login worked, else None
    """
    client = MoodleClient(pool_executor=ThreadPoolExecutor(max_workers=threads or config.getint('Threads')))

    new_credentials = False
    username, password = credentials or (config.get('Username'), None)
    if credentials is None and username is not None:
        new_credentials = False
        password = keyring.get_password('pymoodle-jku', username)
    elif credentials is None:
        # no user configured
        new_credentials = True
        if username is None:
            username = input('Username: ')
        if password is None:
            password = getpass()

    auth = False
    count = 0
    while not auth:
        if count > 2:
            return None
        try:
            auth = client.login(username, password)
        except KeyboardInterrupt:
            return None
        except:
            count += 1
            print('Login failed, trying again...')
            debug('Login failed, trying again...')
    if config.getboolean('SaveQuestion') and new_credentials:
        print('Login Worked ;) Moodle Console mode confirmed!')
        save_password = yn_question(
            'Do you want to store your password in your local keyring (y/n): ')
        if save_password:
            config['Username'] = username
            keyring.set_password('pymoodle-jku', username, password)
        else:
            config['SaveQuestion'] = 'False'
        write_config()
    return client

# neuer user ohne username password -> SaveQuestion True/ new credentials True
# neuer user mit username -> SaveQuestion True/new credentials True
# neuer user mit password -> SaveQuestion True/new credentials True
