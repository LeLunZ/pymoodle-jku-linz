import argparse

from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Utils import grades, downloading
from pymoodle_jku.Utils.login import login
from pymoodle_jku.Utils.printing import clean_screen


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

    parser.add_argument('-u', '--username',
                        help='jku moodle username')
    parser.add_argument('-p', '--password',
                        help='jku moodle password')

    subparsers = parser.add_subparsers(help='Utilities', dest='utility')

    grades_parser = subparsers.add_parser('grades', help='Grading Utility')
    download_parser = subparsers.add_parser('download', help='Download Utility')

    download_parser.add_argument('-p', '--path',
                                 help='Path to download directory. If not specified working directory will be used')
    download_parser.add_argument('-i', '--ids', nargs='?', const=True, default=None,
                                 help='list of course ids to download (seperated by comma 52623,38747,27364). If no id is specified but -i is given you can enter the ids after starting the script (ids will be displayed. This option is avaible even if -q is specified)')

    args = parser.parse_args()
    username, password = None, None
    if args.username:
        username = args.username
    if args.password:
        password = args.password

    client: MoodleClient = login(username=username, password=password, save_password_query=not args.quiet)

    # first use tools
    if 'utility' in args:
        if args.utility == 'grades':
            return grades.main(client, args)
        elif args.utility == 'download':
            return downloading.main(client, args)
    clean_screen()
    return 0


if __name__ == '__main__':
    exit(main())
