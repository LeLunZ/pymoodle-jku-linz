import atexit
import base64
import functools
import logging
import pickle
from concurrent.futures.thread import ThreadPoolExecutor
from getpass import getpass
from typing import Optional

import keyring
from argparse import Namespace
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pymoodle_jku.classes.exceptions import NotLoggedInError
from pymoodle_jku.client.client import MoodleClient
from pymoodle_jku.utils.config_data import config, write_config
from pymoodle_jku.utils.printing import yn_question

logger = logging.getLogger(__name__)

registered = False
f: Fernet = None


def relogin(func):
    @functools.wraps(func)
    def wrapped(client: MoodleClient, args: Namespace):
        try:
            return func(client, args)
        except NotLoggedInError:
            if f is not None:
                client.clear_client()
                config['Session'] = None
                write_config()
                new_client = login(args.credentials, args.threads, client)
                if new_client is None:
                    raise
                else:
                    return func(client, args)
            else:
                raise

    return wrapped


def save_client(client: MoodleClient):
    """
    Saves the Cookies and important data encrypted in the filesystem.
    """
    try:
        if f is not None:
            cookies = client.session.cookies.get_dict()
            sesskey = client.sesskey
            userid = client.userid
            token = f.encrypt(pickle.dumps((cookies, sesskey, userid)))
            config['Session'] = token.decode()
            write_config()
    except (pickle.PicklingError, KeyError, InvalidToken):
        pass


def load_client(client):
    """
    Decodes the encrypted cookies and data from the filesystem.
    """
    token = config['Session']
    if f is not None and token is not None:
        cookies, sesskey, userid = pickle.loads(f.decrypt(token.encode()))
        client.login_with_old_session(cookies, sesskey, userid)
        return True
    return False


def setup_encryption(password):
    global f
    if f is None:
        salt = b'pymoodle-jku'
        backend = default_backend()
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=backend)
        key = base64.urlsafe_b64encode(kdf.derive(bytes(password.encode())))
        f = Fernet(key)


def register_atexit(client):
    global registered
    if registered is False:
        atexit.register(lambda: save_client(client))
        registered = True


def login(credentials, threads: int = None, client: MoodleClient = None) -> Optional[MoodleClient]:
    """
    Tries to Login the user multiple times or uses a .

    :param credentials: Tuple[str, str] with (username, password).
    :param threads: the amount of threads to use for crawling.
    :param client: a prepared MoodleClient.
    :return: A Moodle client if login worked, else None
    """
    client_prepared = client is not None
    client = client or MoodleClient(pool_executor=ThreadPoolExecutor(max_workers=threads or config.getint('Threads')))

    new_credentials = False
    username, password = credentials or (config.get('Username'), None)
    if credentials is None and username is not None:
        new_credentials = False
        password = keyring.get_password('pymoodle-jku', username)

        setup_encryption(password)
        register_atexit(client)
        if not client_prepared:
            try:
                auth = load_client(client)
            except (KeyError, pickle.UnpicklingError, InvalidToken, AttributeError):
                auth = False
            if auth:
                return client
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
        except NotLoggedInError:
            print('Login failed, trying again...')
        count += 1
    if config.getboolean('SaveQuestion') and new_credentials:
        print('Login Worked ;) Moodle Console mode confirmed!')
        save_password = yn_question(
            'Do you want to store your password in your local keyring?')
        if save_password:
            config['Username'] = username
            keyring.set_password('pymoodle-jku', username, password)
            setup_encryption(password)
            register_atexit(client)
        else:
            config['SaveQuestion'] = 'False'
        write_config()
    register_atexit(client)
    return client
