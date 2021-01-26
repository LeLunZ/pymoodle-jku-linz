import argparse
from pathlib import Path

from pymoodle_jku.Utils.downloading import download
from pymoodle_jku.Utils.login import login


def print_courses(client):
    courses = client.courses_overview()
    output = '\n'.join(map(lambda c: f'{c.id}: {c.fullname}', courses))
    print(output, flush=True)


def main():
    parser = argparse.ArgumentParser(description='Download moodle files')
    parser.add_argument('-d', '--download',
                        help='path to download directory')
    parser.add_argument('-c', '--courses', action='store_true',
                        help='list all courses with its ids')
    parser.add_argument('-i', '--ids', nargs='?', const=True, default=None,
                        help='list of course ids to download (seperated by comma 52623,38747,27364). If no id is specified but -i is given you can enter the ids after starting the script (ids will be displayed)')
    parser.add_argument('-u', '--username',
                        help='jku moodle username')
    parser.add_argument('-p', '--password',
                        help='jku moodle password')

    args = parser.parse_args()
    username, password = None, None
    if args.username:
        username = args.username
    if args.password:
        password = args.password

    client = login(username=username, password=password)

    if args.courses:
        print_courses(client)
    if args.download:
        if args.ids is True:
            if not args.courses:
                print_courses(client)
            download(Path(args.download), client, ids=True)
        if type(args.ids) is str:
            ids = list(map(lambda i: int(i), args.ids.split(',')))
            download(Path(args.download), client, ids=ids)
            return 0
        download(Path(args.download), client)
        return 0

    return 0


if __name__ == '__main__':
    exit(main())
