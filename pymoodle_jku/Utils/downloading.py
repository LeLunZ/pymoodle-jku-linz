import logging
from pathlib import Path
from typing import Union, List

from pick import pick

from pymoodle_jku.Classes.course_data import Url
from pymoodle_jku.Classes.evaluation import Evaluation
from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Client.download_manager import DownloadManager

logger = logging.getLogger(__name__)


def debug(msg):
    logger.debug(f'UniJob: {msg}')


def get_all_downloads(dir_, links: List[Union[Url, Evaluation]]):
    url_list = dir_ / 'urls.txt'
    try:
        urls = url_list.read_text().split('\n')
        f = list(filter(lambda l: l.link if type(l) is Url else l.url not in urls, links))
        return (f, urls)
    except:
        return (links, [])


def write_urls(dir_, urls):
    url_list = dir_ / 'urls.txt'
    url_list.write_text('\n'.join(urls))


def main(client: MoodleClient, args):
    path = Path('./' if args.path is None else args.path)

    ids = None
    if args.ids is True:
        courses = list(client.courses(load_page=False))
        selected = pick(list(map(lambda c: f'{c.id}: {c.fullname}', courses)), multiselect=True, min_selection_count=0)
        if len(selected) == 0:
            exit(0)
        ids = [courses[i].id for o, i in selected]
    if type(args.ids) is str:
        ids = list(map(lambda i: int(i), args.ids.split(',')))

    courses = client.courses(filter_ids=ids)

    for c in courses:
        cur_dir = path / (c.fullname.split(',')[1].strip())
        try:
            cur_dir.mkdir()
        except:
            pass

        valuations = client.single_valuation_overview(c)
        all_links = c.course_page.to_course_data().links + valuations

        new_urls, old_urls = get_all_downloads(path, all_links)

        dm = DownloadManager(all_links, client, path=cur_dir)
        dm.download()

        finished_url = old_urls + [u for u, f in dm.done]

        write_urls(path, finished_url)
        del dm

        debug(f'done with {c.shortname}')


if __name__ == "__main__":
    # Change to your download folder
    # something like ./Courses
    # The folder must exist already
    # and the path must be relative to where you start the process
    # or you can specify an absolut path
    try:
        pass
    except Exception as err:
        debug(str(err))
