from distutils.util import strtobool
from getpass import getpass
from pathlib import Path
import configparser

import keyring
from keyring.errors import PasswordDeleteError
from pick import pick
from pymoodle_jku.Utils.printing import clean_screen, yn_question

cp = configparser.ConfigParser(allow_no_value=True)
config_file = Path.home() / '.pymoodle'

if config_file.is_file():
    cp.read(config_file)
else:
    cp['DEFAULT'] = {'Threads': '6', 'Path': None, 'Username': None, 'SaveQuestion': 'True'}

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
    config['Username'] = username
    keyring.set_password('pymoodle-jku', username, password)


def main(args):
    interactive = True
    if args.threads:
        interactive = False
        config['Threads'] = args.threads
    if args.directory:
        interactive = False
        config['Path'] = args.path
    if args.credentials:
        interactive = False
        set_new_user(args.credentials)

    if interactive:
        while True:
            clean_screen()
            option, idx = pick([f'Set Credentials ({config["Username"]})',
                                f'Set default download directory. If its None, current directory will be used ({config["Path"]})',
                                f'Set Max Threads ({config["Threads"]})',
                                f'Set if "Save Password" Question should be asked when password is entered while running another Utility ({"Yes" if config.getboolean("SaveQuestion") else "No"})',
                                f'Clear PyMoodle installation',
                                'Exit'])
            if idx == 0:
                username = input('Username: ')
                password = getpass()
                set_new_user((username, password))
            elif idx == 1:
                storage = input('Directory: ')
                if storage == '':
                    config['Path'] = None
                else:
                    storage_path = Path(storage).resolve()
                    if not storage_path.is_dir() and storage_path.parent.is_dir():
                        storage_path.mkdir()
                    elif not storage_path.is_dir():
                        raise Exception('Directory doesn\'t exist.')
                    config['Path'] = str(storage_path)
            elif idx == 2:
                threads = int(input('Max Threads: '))
                config['Threads'] = str(threads)
            elif idx == 3:
                save_password = yn_question('Save Password Question (y/n):')
                config['SaveQuestion'] = str(save_password)
            elif idx == 4:
                delete_config = yn_question(
                    'Password and config will be deleted. Downloaded files wont!\nAre you sure? (y/n): ')
                if delete_config:
                    try:
                        keyring.delete_password('pymoodle-jku', config['Username'])
                        config_file.unlink()
                        break
                    except PasswordDeleteError:
                        pass
                    except FileNotFoundError:
                        pass
                    finally:
                        print(
                            'Everything Deleted. When running PyMoodle again, a new (default) config will be created.')
                        return 0
            elif idx == 5:
                break
            write_config()
    else:
        write_config()
    return 0
