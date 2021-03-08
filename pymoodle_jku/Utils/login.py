import atexit
import base64
import logging
import pickle
from concurrent.futures.thread import ThreadPoolExecutor
from getpass import getpass
from typing import Optional

import keyring
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pymoodle_jku.Classes.exceptions import LoginError
from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Utils.config import config, write_config
from pymoodle_jku.Utils.printing import yn_question

logger = logging.getLogger(__name__)

f: Fernet = None


def save_client(client):
    try:
        if config['Username'] is not None:
            cookies = client.session.cookies.get_dict()
            sesskey = client.sesskey
            userid = client.userid
            token = f.encrypt(pickle.dumps((cookies, sesskey, userid)))
            config['Session'] = token.decode()
            write_config()
    except Exception:
        pass


def load_client(client):
    if config['Username'] is not None:
        token = config['Session']
        cookies, sesskey, userid = pickle.loads(f.decrypt(token.encode()))
        return client.login_with_old_session(cookies, sesskey, userid)
    return False


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
    loaded_from_keyring = False
    if credentials is None and username is not None:
        new_credentials = False
        password = keyring.get_password('pymoodle-jku', username)
        loaded_from_keyring = True
    elif credentials is None:
        # no user configured
        new_credentials = True
        if username is None:
            username = input('Username: ')
        if password is None:
            password = getpass()

    auth = False
    count = 0
    # create Fernet
    salt = b'pymoodle-jku'
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(bytes(password.encode())))
    global f
    f = Fernet(key)

    while not auth:
        if count > 2:
            return None
        try:
            if loaded_from_keyring:
                try:
                    auth = load_client(client)
                except (KeyError, pickle.UnpicklingError, InvalidToken):
                    auth = False
                loaded_from_keyring = False
            else:
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
    atexit.register(lambda: save_client(client))
    return client
