import argparse
from pathlib import Path

from pymoodle_jku.Utils.downloading import download

parser = argparse.ArgumentParser(description='Download moodle files')
parser.add_argument('-d', '--download',
                    help='path to download directory')
parser.add_argument('-u', '--username',
                    help='jku moodle username')
parser.add_argument('-p', '--password',
                    help='jku moodle password')

args = parser.parse_args()

if args.download:
    username, password = None, None
    if args.username:
        username = args.username
    if args.password:
        password = args.password
    download(Path(args.download), username=username, password=password)
