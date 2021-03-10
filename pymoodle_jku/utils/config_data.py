import configparser
from pathlib import Path

import keyring
from keyring.errors import PasswordDeleteError

cp = configparser.ConfigParser(allow_no_value=True)
config_file = Path.home() / '.pymoodle'

cp['DEFAULT'] = {'Threads': '6', 'Path': None, 'Username': None, 'SaveQuestion': 'True', 'Session': None,
                 'UpdateInfo': 'True'}
if config_file.is_file():
    cp.read(config_file)

config = cp['DEFAULT']


def write_config() -> None:
    """
    Writes the config to the .pymoodle file.
    :return:
    """
    with open(config_file, 'w') as f:
        cp.write(f)


def set_new_user(credentials) -> None:
    """
    Saves new user credentials.
    User is stored in the config.
    Password is stored in the keyring.
    :param credentials: a tuple of (username, password)
    :return:
    """
    username, password = credentials
    if config['Username'] is not None:
        try:
            keyring.delete_password('pymoodle-jku', config['Username'])
        except PasswordDeleteError:
            pass
    config['Session'] = None
    config['Username'] = username
    keyring.set_password('pymoodle-jku', username, password)
