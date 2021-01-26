import logging

from pathlib import Path
from pymoodle_jku.Classes.course_data import Url
from pymoodle_jku.Client.client import DownloadManager
from pymoodle_jku.Utils.login import login

logger = logging.getLogger(__name__)


def debug(msg):
    logger.debug(f'UniJob: {msg}')


def get_all_downloads(dir_, links: [Url]):
    url_list = dir_ / 'urls.txt'
    try:
        urls = url_list.read_text().split('\n')
        f = list(filter(lambda l: l.link not in urls, links))
        return (f, urls)
    except:
        return (links, [])


def write_urls(dir_, urls):
    url_list = dir_ / 'urls.txt'
    url_list.write_text('\n'.join(urls))


def input_id():
    return input('Course id (enter to continue): ').strip()


def download(dir_, client=None, ids=False):
    if client is None:
        client = login()
    try:
        dir_.mkdir()
    except:
        pass
    courses = client.courses_overview()
    if ids is not False:
        course_ids = []
        if ids is True:
            inp = input_id()
            while inp != '':
                course_ids.append(int(inp))
                inp = input_id()
        elif type(ids) is list:
            course_ids = ids
        courses = list(filter(lambda c: c.id in course_ids,courses))
    for c in client.courses(courses):
        cur_dir = dir_ / (c.course.fullname.split(',')[1].strip())
        try:
            cur_dir.mkdir()
        except:
            pass

        new_urls, old_urls = get_all_downloads(dir_, c.links)
        dm = DownloadManager(new_urls, client, cur_dir)

        dm.download()

        finished_url = old_urls + dm.done

        write_urls(dir_, finished_url)
        del dm

        debug(f'done with {c.course.shortname}')


if __name__ == "__main__":
    # Change to your download folder
    # something like ./Courses
    # The folder must exist already
    # and the path must be relative to where you start the process
    # or you can specify an absolut path
    try:
        download(Path('./tmp'))
    except Exception as err:
        debug(str(err))
