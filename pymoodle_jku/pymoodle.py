import signal
import sys
import argparse

import argcomplete


def interuppt_handler(signum, frame):
    sys.exit(0)


def check_update():
    from pymoodle_jku.utils.config_data import config
    updates = config.getboolean('UpdateInfo')
    if updates:
        from importlib.metadata import version
        import requests
        from requests import RequestException
        from packaging.version import parse as parse_version
        from sty import fg
        from json.decoder import JSONDecodeError
        from importlib.metadata import PackageNotFoundError

        package = 'pymoodle-jku'
        repo_url = f'LeLunZ/{package}-linz'
        try:
            installed_version = version(package)
            response = requests.get(f'https://api.github.com/repos/{repo_url}/releases/latest')
            current_version = response.json()['tag_name']
            c_version = parse_version(current_version)
            i_version = parse_version(installed_version)
            if i_version < c_version:
                print(fg.li_red + 'New Version is available!' + fg.rs)
                print(
                    fg.li_red + 'Install with python3 >= 3.8 pip: ' + fg.rs + fg.li_blue + f'pip install -U pymoodle-jku=={current_version}' + fg.rs)
                print(
                    fg.li_red + 'Use pip3 if you have python2 on the system: ' + fg.rs + fg.li_green + f'pip3 install -U pymoodle-jku=={current_version}' + fg.rs)
        except RequestException:
            pass
        except JSONDecodeError:
            pass
        except PackageNotFoundError:
            pass


def main():
    parser = argparse.ArgumentParser(description='Python JKU Moodle Utility', usage='pymoodle [-options] {Utility}')
    # interactive -> https://pypi.python.org/pypi/pick
    #   > show grades
    #   > show all evaluations of one course
    #   > download all
    #   > download specific courses/excercises or tests
    #
    # parser.add_argument('toolname', default=None,
    #                     const=None,
    #                     nargs='?', choices=['grades', 'download', 'courses', None],
    #                     help='the name of the tool to be used')

    parser.add_argument('-q', '--quiet', action='store_true',
                        help='the script will ask for no input (useful in Docker environments)')

    parser.add_argument('-t', '--threads', default=8, type=int,
                        help='max amount of threads to use for crawling. Value doesn\t persist. See config for more.')
    parser.add_argument('-c', '--credentials', nargs=2, metavar=('username', 'password'),
                        help='JKU username and password. (Optional, if not provided you will be asked to Enter it)')

    subparsers = parser.add_subparsers(help='Utilities', dest='utility')

    grades_parser = subparsers.add_parser('grades', help='Grading Utility')

    grades_parser.add_argument('-s', '--search', action='append',
                               help='Search for courses with given string in its name. Evaluations of it will be printed if found')

    grades_parser.add_argument('-o', '--old', action='store_true', help='Use if you want to show finished courses.')

    download_parser = subparsers.add_parser('download', help='Download Utility')

    download_parser.add_argument('-p', '--path',
                                 help='Path to download directory. If not specified working directory will be used')
    # download_parser.add_argument('-s', '--search', nargs='?', action='append',
    #                              const=True, default=False,
    #                              help='Searches for courses to download. If no input is specified it will asks the user to select courses.')

    download_parser.add_argument('-s', '--search', action='append',
                                 help='Search and downloads courses with given string in its name. Can\'t be used with [-i]')

    download_parser.add_argument('-a', '--all', action='store_true',
                                 help='Downloads all courses of the current semester. If run with [-o] all courses from older semesters get downloaded.')

    download_parser.add_argument('-e', '--exams', action='store_true',
                                 help='Will download only Exams, even if they are already in urls.txt. This option exists because previously exam urls were written into urls.txt but exams werent downloaded. This option will also get removed at the end of next semester.')

    download_parser.add_argument('-o', '--old', action='store_true',
                                 help='Use if you want to download old courses.')

    timeline_parser = subparsers.add_parser('timeline', help='Timeline Utility')

    timeline_parser.add_argument('-l', '--limit', default=15, type=int, help='The max amount of Events to show.')

    config_parser = subparsers.add_parser('config',
                                          help='Changes default values. Don\'t specifying an argument will invoke iteractive mode.')

    config_parser.add_argument('-d', '--directory',
                               help='Sets default Directory for downloads, if not specified, current directory will dertermine the location. Using [--path] when using {download} will not overwrite this once, but it will not persist.')

    config_parser.add_argument('-t', '--threads',
                               help='Changes max amount of Threads used for crawling.')

    config_parser.add_argument('-c', '--credentials',
                               help='Sets the moodle credentials.')

    argcomplete.autocomplete(parser)

    args = parser.parse_args()

    # imports are here because autocomplete is faster that way
    import sys
    import atexit
    import logging

    from sty import fg

    from pymoodle_jku.utils import basic
    from pymoodle_jku.client.client import MoodleClient
    from pymoodle_jku.utils import grades, downloading, timetable, config
    from pymoodle_jku.utils import login
    from pymoodle_jku.classes.exceptions import LoginError
    from pymoodle_jku.utils.printing import yn_question
    logger = logging.getLogger(__name__)

    logger.debug('PyMoodle start')
    atexit.register(check_update)
    signal.signal(signal.SIGINT, interuppt_handler)

    supported_version = (3, 8)
    supported_version_str = 'Python >=3.8'
    if sys.version_info < supported_version:
        print(fg.li_red + 'You aren\'t running a supported Python version. There could be some bugs while running.')
        print(f'For full support install {supported_version_str}' + fg.rs)
        continue_pymoodle = yn_question(input(fg.li_blue + 'Do you still want to continue?' + fg.rs))
        if not continue_pymoodle:
            return 0

    if 'utility' not in args or args.utility is None:
        all_parser = [config_parser, grades_parser, download_parser, timeline_parser, parser]
        return basic.main(all_parser)

    elif 'utility' in args and args.utility is not None:
        if args.utility == 'config':
            return config.main(args)

        client: MoodleClient = login.login(credentials=args.credentials,
                                           threads=args.threads)

        if client is None:
            raise LoginError('Try again. Login Failed.')
        if args.utility == 'grades':
            return grades.main(client, args)
        elif args.utility == 'download':
            return downloading.main(client, args)
        elif args.utility == 'timeline':
            return timetable.main(client, args)
    else:
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
