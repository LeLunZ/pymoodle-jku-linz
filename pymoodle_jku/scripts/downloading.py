import logging
import time
from pathlib import Path
from typing import Union, List, Tuple

from sty import fg
import atexit

from pymoodle_jku.classes.course_data import Url, UrlType
from pymoodle_jku.classes.evaluation import Evaluation
from pymoodle_jku.client.client import MoodleClient
from pymoodle_jku.client.download_manager import DownloadManager
from pymoodle_jku.utils.config import config
from pymoodle_jku.utils.login import relogin
from pymoodle_jku.utils.net_usage import net_interfaces
from pymoodle_jku.utils.printing import print_pick_results_table

logger = logging.getLogger(__name__)


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
        urls = url_list.read_text().splitlines()
        f = list(filter(lambda l: l.link not in urls, links))
        return f, urls
    except FileNotFoundError:
        return links, []


def write_urls(dir_: Path, urls: List[str]) -> None:
    """
    Writes the given urls to the urls.txt.
    :param dir_:
    :param urls:
    :return:
    """
    url_list = dir_ / 'urls.txt'
    url_list.write_text('\n'.join(urls))


def handle_exit(dl_manager: DownloadManager, path: Path, old_urls: List[str]) -> None:
    done = [(d[1], d[2]) for d in dl_manager.get_done_futures() if d[0]]
    finished_url = old_urls + [u for u, f in done]

    write_urls(path, finished_url)


@relogin
def main(client: MoodleClient, args):
    path = args.path or config['Path']
    path = Path('./' if path is None else path)
    now = time.time()

    def filter_new(c, t=now, old=args.old):
        if not old:
            return c.enddate >= t or c.enddate is None or c.enddate == 0
        else:
            return True

    if args.search and args.all:
        print('Search parameters can\'t be used when using all mode.')
        return 0
    elif args.search is not None:
        courses = client.courses(
            filter_exp=lambda c, search=args.search: any(
                s.lower() in c.fullname.lower() for s in search) and filter_new(c))
    elif args.all or args.quiet:
        courses = client.courses(filter_exp=filter_new)
    else:
        loaded_more = False
        courses = list(client.courses(load_pages=False, filter_exp=filter_new))
        if len(courses) == 0:
            print('No Courses to download. Try [-o] for older courses.')
            return 0
        while True:
            selected = print_pick_results_table([(c.parse_name(),) for c in courses], multiselect=True)
            if type(selected) is tuple:
                option, index = selected
                if index == -1:
                    return 0
                if index == -2:
                    if not args.old and not loaded_more:
                        loaded_more = True
                        courses = list(client.courses(load_pages=False))
            else:
                break
        picked_courses = [courses[idx] for v, idx in selected]
        courses = client.courses(load_pages=picked_courses)

    count = 0
    start = time.time()

    if args.interface is None:
        net_inter = net_interfaces()
        network_interface = print_pick_results_table([[e] for e in net_inter], False, False)
        interface = net_inter[network_interface[1]]
    else:
        interface = args.interface
    download_speed = args.speed or float(input('Download Speed in Mbit/s: '))

    for c in list(courses):
        print('Starting with Course: ' + c.parse_name())
        count += 1
        cur_dir = path / (c.parse_name())
        try:
            cur_dir.mkdir()
        except (FileNotFoundError, OSError):
            pass

        valuations = [v.url for v in client.single_valuation(c)]

        all_links = c.course_page.to_course_data().links + valuations
        new_urls, old_urls = get_all_downloads(path, all_links)

        dm = DownloadManager(new_urls, client, path=cur_dir, download_speed=download_speed, net_interface=interface)
        atexit.register(handle_exit, dm, path, old_urls)
        try:
            dm.download()
        except KeyboardInterrupt:
            return 0

        atexit.unregister(handle_exit)
        finished_url = old_urls + [u for u, f in dm.done]

        write_urls(path, finished_url)
        del dm

        print(fg.li_green + f'Done with {c.parse_name()}' + fg.rs)

    end = time.time()
    print(f'{(end - start) / 60} minutes runtime')
    if count == 0:
        print('No Courses to download. Try [-o] for older courses.')

    return 0


if __name__ == "__main__":
    # Change to your download folder
    # something like ./Courses
    # The folder must exist already
    # and the path must be relative to where you start the process
    # or you can specify an absolut path
    pass
