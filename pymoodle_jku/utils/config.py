from getpass import getpass
from pathlib import Path

import keyring
from keyring.errors import PasswordDeleteError
from pick import pick

from pymoodle_jku.classes.exceptions import LoginError
from pymoodle_jku.client.client import MoodleClient
from pymoodle_jku.utils.config_data import config, set_new_user, write_config, config_file
from pymoodle_jku.utils.printing import clean_screen, yn_question


def build_questions():
    questions = ['Set credentials' if config['Username'] is None else 'Change Credentials',
                 f'Set default download directory, if not set the directory where you run pymoodle will be used.' if
                 config[
                     'Path'] is None else f'Change or disable default download directory ({Path(config["Path"])})',
                 f'Set max amount of Threads to use for crawling ({config["Threads"]})',
                 f'Disable Save Password Question for new user' if config.getboolean(
                     'SaveQuestion') else 'Enable Save Password Question for new user',
                 f'Disable check for updates' if config.getboolean('UpdateInfo') else 'Enable check for updates',
                 'Remove PyMoodle installation (config & keyring)', 'Exit']

    return questions


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

            questions = build_questions()
            option, idx = pick(questions)
            if idx == 0:
                username = input('Username: ')
                password = getpass()
                count = 0
                auth = False
                while count < 3:
                    try:
                        auth = MoodleClient().login(username, password)
                    except LoginError:
                        auth = False
                    if auth:
                        break
                    count += 1
                if auth:
                    set_new_user((username, password))
                else:
                    input('Login failed, press [Enter] and try again')
            elif idx == 1:
                storage = input('Directory (leave empty to reset): ')
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
                try:
                    threads = int(input('Max Threads: '))
                    config['Threads'] = str(threads)
                except ValueError:
                    pass
            elif idx == 3:
                question = 'Disable?' if config.getboolean('SaveQuestion') else 'Enable?'
                save_password = yn_question(question)
                if save_password:
                    config['SaveQuestion'] = str(not config.getboolean('SaveQuestion'))
            elif idx == 4:
                question = 'Disable?' if config.getboolean('UpdateInfo') else 'Enable?'
                save_password = yn_question(question)
                if save_password:
                    config['UpdateInfo'] = str(not config.getboolean('UpdateInfo'))
            elif idx == 5:
                delete_config = yn_question(
                    'Password and config will be deleted. Downloaded files wont!\nAre you sure?')
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
            elif idx == 6:
                break
            write_config()
    else:
        write_config()
    return 0
