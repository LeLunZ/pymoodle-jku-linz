import logging
import time
from pathlib import Path
from typing import Union, List, Tuple

from pymoodle_jku.Classes.course_data import Url
from pymoodle_jku.Classes.evaluation import Evaluation
from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Client.download_manager import DownloadManager
from pymoodle_jku.Utils.config import config
from pymoodle_jku.Utils.printing import print_pick_results_table

logger = logging.getLogger(__name__)


def debug(msg):
    logger.debug(f'UniJob: {msg}')


def get_all_downloads(dir_: Path, links: List[Union[Url, Evaluation]]) -> Tuple[
    List[Union[Url, Evaluation]], List[str]]:
    '''
    Compares the urls from urls.txt with [links].
    :param dir_: the directory where urls.txt is stored.
    :param links: A list of Urls or Evaluations from where to get the urls
    :return: The new urls which are not found in urls.txt
    '''
    url_list = dir_ / 'urls.txt'
    try:
        urls = url_list.read_text().split('\n')
        f = list(filter(lambda l: l.link if type(l) is Url else l.url not in urls, links))
        return (f, urls)
    except:
        return (links, [])


def write_urls(dir_: Path, urls: List[str]) -> None:
    """
    Writes the given urls to the urls.txt.
    :param dir_:
    :param urls:
    :return:
    """
    url_list = dir_ / 'urls.txt'
    url_list.write_text('\n'.join(urls))


def main(client: MoodleClient, args):
    path = args.path or config['Path']
    path = Path('./' if path is None else path)
    now = time.time()

    def filter_new(c, t=now, old=args.old):
        if not old:
            return c.enddate >= t
        else:
            return True

    if args.search and args.interactive:
        print('Search parameters can\'t be used when using interactive search mode.')
        exit(0)
    if args.interactive is True:
        if args.quiet:
            print('Interactive mode can\'t be used while being quiet mode.')
            exit(0)
        loaded_more = False
        courses = list(client.courses(load_pages=False, filter_exp=filter_new))
        if len(courses) == 0:
            print('No Courses to download. Try [-o] for older courses.')
            exit(0)
        while True:
            selected = print_pick_results_table([(c.parse_name(),) for c in courses], multiselect=True)
            if type(selected) is tuple:
                option, index = selected
                if index == -1:
                    exit(0)
                if index == -2:
                    if not args.old and not loaded_more:
                        loaded_more = True
                        courses = client.courses(load_pages=False)
            else:
                break
        picked_courses = [courses[idx] for v, idx in selected]
        courses = client.courses(load_pages=picked_courses)
    elif args.search is not None:
        courses = client.courses(
            filter_exp=lambda c, search=args.search: any(
                s.lower() in c.fullname.lower() for s in search) and filter_new(c))
    else:
        courses = client.courses(filter_exp=filter_new)

    count = 0
    for c in courses:
        count += 1
        cur_dir = path / (c.parse_name())
        try:
            cur_dir.mkdir()
        except:
            pass

        valuations = client.single_valuation(c)
        if args.exams:
            all_links = valuations
            new_urls, old_urls = get_all_downloads(path, all_links)
            new_urls = all_links
        else:
            all_links = c.course_page.to_course_data().links + valuations
            new_urls, old_urls = get_all_downloads(path, all_links)

        dm = DownloadManager(new_urls, client, path=cur_dir)
        dm.download()

        finished_url = old_urls + [u for u, f in dm.done]

        write_urls(path, finished_url)
        del dm

        debug(f'done with {c.shortname}')

    if count == 0:
        print('No Courses to download. Try [-o] for older courses.')


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
