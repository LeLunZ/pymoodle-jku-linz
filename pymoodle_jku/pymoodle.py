import argparse

from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Utils import grades, downloading, timetable
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

    parser.add_argument('-t', '--threads', default=6, type=int,
                        help='max amount of threads to use for crawling')
    parser.add_argument('-u', '--username',
                        help='jku moodle username')
    parser.add_argument('-p', '--password',
                        help='jku moodle password')

    subparsers = parser.add_subparsers(help='Utilities', dest='utility')

    grades_parser = subparsers.add_parser('grades', help='Grading Utility')

    grades_parser.add_argument('-s', '--search', action='append',
                               help='Search for a course. Evaluations of it will be printed if found')

    download_parser = subparsers.add_parser('download', help='Download Utility')

    download_parser.add_argument('-p', '--path',
                                 help='Path to download directory. If not specified working directory will be used')
    # download_parser.add_argument('-s', '--search', nargs='?', action='append',
    #                              const=True, default=False,
    #                              help='Searches for courses to download. If no input is specified it will asks the user to select courses.')

    download_parser.add_argument('-s', '--search', action='append',
                                 help='Searches for courses to download. Can\'t be used with [-i]')
    download_parser.add_argument('-i', '--interactive', action='store_true',
                                 help='You can pick courses later. Can\'t be used with [-s] or in quiet mode [-q].')

    download_parser.add_argument('-e', '--exams', action='store_true',
                                 help='Will download only Exams, even if they are already in urls.txt. This option exists because previously exam urls were written into urls.txt but exams werent downloaded. This option will also get removed at the end of next semester.')

    timeline_parser = subparsers.add_parser('timeline', help='Timeline Utility')

    args = parser.parse_args()

    username, password = None, None
    if args.username:
        username = args.username
    if args.password:
        password = args.password

    client: MoodleClient = login(username=username, password=password, save_password_query=not args.quiet,
                                 threads=args.threads)

    # first use tools
    if 'utility' in args:
        if args.utility == 'grades':
            return grades.main(client, args)
        elif args.utility == 'download':
            return downloading.main(client, args)
        elif args.utility == 'timeline':
            return timetable.main(client, args)
    clean_screen()
    return 0


if __name__ == '__main__':
    exit(main())
