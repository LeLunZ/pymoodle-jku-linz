import logging
import re
import subprocess
import time
import traceback
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from typing import Tuple, Optional, List
from urllib.parse import unquote, urlparse

import iouuid
from lxml import html
from pytube import YouTube

from pymoodle_jku.classes.course_data import UrlType, Url
from pymoodle_jku.classes.evaluation import Evaluation
from pymoodle_jku.client.client import MoodleClient
from pymoodle_jku.client.html_parser import QuizSummary, QuizPage
from pymoodle_jku.utils.printing import print_exc

logger = logging.getLogger(__name__)


def rsuffix(suffix) -> str:
    """Returns a new suffix for some files.
    Currently if will replace .m3u or .m3u8 with mp4.

    :param suffix: The suffix that should be checked
    :return: Returns the old or replaced suffix.
    """
    if suffix.startswith('.m3u8') or suffix.startswith('.m3u'):
        return '.mp4'
    else:
        return suffix


class DownloadManager:
    def __init__(self, urls, client: 'MoodleClient', path):
        """Takes Objects which should be downloaded with a Moodle client.

        :param urls: A List of Objects to download. The DownloadManager will check if these are downloadable.
        :param client: A instance of a MoodleClient, that should be logged in.
        :param path: The directory where downloads are stored.
        """
        self.urls = urls
        self.failed = []
        self.done: List[Tuple[str, Path]] = []
        self.client = client
        self.path = Path(path)

    def get_request(self, url):
        """Sends a GET requests to download files.

        :param url: Link to a file.
        :return: Calls process_response on return.
        """
        response = self.client.session.get(url, stream=True)
        return self.process_response(url, response)

    def post_request(self, url):
        """Sends a POST request to download files.

        :param url: Link to a file.
        :return: Calls process_response on return.
        """
        response = self.client.session.post('https://moodle.jku.at/jku/mod/folder/download_folder.php',
                                            data={'id': url.split('id=')[1].split('&')[0],
                                                  'sesskey': self.client.sesskey}, stream=True)
        return self.process_response(url, response)

    def download_evaluation(self, l) -> Tuple[bool, str, Optional[Path]]:
        """Downloads a Evaluation or Url.Quiz Object.

        :param l: Evaluation or Url to download.
        :return: A Tuple that describes the download (finished,url,path).
        """
        if type(l) is Evaluation:
            weblink = l.url
            response = self.client.session.get(l.url)
        elif type(l) is Url:
            weblink = l.link
            response = self.client.session.get(l.link)
        else:
            raise Exception('wrong class')  # TODO Add other exception type
        q_page = QuizSummary(response)
        u = q_page.quiz_url()
        if u is None:
            return False, weblink, None

        response = self.client.session.get(u.link)

        qz_page = QuizPage(response)
        output = qz_page.md_quiz()

        name = re.sub('[^\w\-_\.\(\) ]', '', l.name)
        name = re.sub('[ ]', '_', name)

        images = [im for im in qz_page.images if im in output and 'jku.at' in urlparse(str(im)).hostname]
        if len(qz_page.images) > 0:
            d_path = self.path / name
            try:
                d_path.mkdir()
            except (FileNotFoundError, OSError):
                pass

            for i in images:
                response = self.client.session.get(str(i), stream=True)
                link, done, file = self.process_response(str(i), response, path=d_path)
                if file is not None:
                    output = output.replace(i, str(file.relative_to(self.path)))

        filename = iouuid.generate_id(self.path / f'{name}.md', size=2)

        with open(self.path / filename, 'w', encoding="utf-8") as f:
            f.write(output)

        # HTML(string=html_str.decode('utf-8')).write_pdf(filename)
        # pdfkit.from_string(html_str.decode('utf-8'), filename)

        return True, weblink, self.path / filename

    def _prepare_download_source(self, l):
        """
        Calls the corresponding method for the object l if l is downloadable.
        """
        try:
            if type(l) is Evaluation or l.type is UrlType.Quiz:
                return self.download_evaluation(l)
            if l.type is UrlType.Resource:
                return self.get_request(l.link)
            elif l.type is UrlType.Folder:
                return self.post_request(l.link)
            elif l.type is UrlType.Streamurl:
                return self._download_stream(l)
            elif l.type is UrlType.Url:
                return self.download_from_url(l.link)
            else:
                # return false because if we later add the datatype we still want to download it.
                def return_false(l):
                    return False, l.link, None

                return return_false(l)
        except (SystemExit, KeyboardInterrupt, GeneratorExit):
            raise
        except Exception:
            # Never let any exception go outside of this. So that we can always return a failed download.
            # traceback.print_exc()
            website = l.url if type(l) is Evaluation else l.link
            if type(l) is Evaluation:
                return False, l.url, None
            return False, l.link, None

    def download(self) -> None:
        """Downloads the urls to the path in the filesystem.
        Finished downloads are stored in self.done as Tuple[str, Path] (url, file).

        :return: Nothing
        """
        lengths = len(self.urls)
        with ThreadPoolExecutor() as executor:
            print(f"Downloading {len(self.urls)} items")
            futures = [executor.submit(self._prepare_download_source, url) for url in self.urls]
            for f in as_completed(futures):
                try:
                    done, url, file = f.result()
                    logger.info(f'received: {url}')
                    if done:
                        self.done.append((url, file))
                    else:
                        self.failed.append(url)
                except (SystemExit, KeyboardInterrupt, GeneratorExit) as err:
                    raise
                except Exception as e:
                    print_exc(e)
                    logger.error(e)
                print(f'{len(self.done) + len(self.failed)}/{lengths}', end='\r')

    def download_from_url(self, url) -> Tuple[bool, str, Optional[Path]]:
        """Downloads a file from a url. If its a moodle url it will call process_response with the response object.
        If its a youtube link it will download it with pytube.

        :param url: Link to the Download.
        :return: A Tuple that describes the download (finished,url,path).
        """
        p = Path(url)
        link = url
        if '?' in p.name and '=' in p.name:  # doing this for moodle download
            link += '&forcedownload=1&redirect=1'  # normally every other server ignores this
        else:
            link += '?forcedownload=1&redirect=1'
        response = self.client.session.get(link, stream=True)
        if response.url.startswith('https://www.youtube.com/watch') or response.url.startswith(
                'youtube.com/watch') or response.url.startswith('https://youtube.com/watch'):
            youtube = YouTube(response.url)
            response.close()
            highest_res_stream = youtube.streams.filter(resolution='720p', progressive=True, file_extension='mp4')
            if len(highest_res_stream) == 0:
                highest_res_stream = youtube.streams.filter(progressive=True, file_extension='mp4').order_by(
                    'resolution').desc()
                if len(highest_res_stream) != 0:
                    download_obj = highest_res_stream[0]
                else:
                    return False, url, None
            else:
                download_obj = highest_res_stream.order_by('fps')[-1]

            filename = download_obj.default_filename
            filename = iouuid.generate_id(self.path / filename, size=2)
            download_obj.download(output_path=self.path, filename=Path(filename).stem)
            return True, url, self.path / filename
        else:
            return self.process_response(url, response)

    def process_response(self, url, response, path=None) -> Tuple[bool, str, Optional[Path]]:
        """Processes a Response object from a given url.
        It takes the content as chunks and writes it to the filesystem.

        :param url: The url for the response.
        :param response: A response object of a request.
        :param path: A Path where the file should be stored.
        :return: A Tuple that describes the download (finished,url,path).
        """
        if (cnt_dis := response.headers.get('Content-Disposition')) is not None:
            filename = cnt_dis.split('filename="')[1][:-1]
            size = 1024 * 1024
            chunk = next(response.iter_content(chunk_size=size))
            try:
                data = chunk.decode()
                m = 'w'
            except (UnicodeDecodeError, AttributeError):
                m = 'wb'
                data = chunk
            if path is None:
                path = self.path
            filename = iouuid.generate_id(path / filename, size=2)
            with open(path / filename, m) as file:
                file.write(data)
                for chunk in response.iter_content(chunk_size=size):
                    file.write(chunk)
            del data
            return True, url, path / filename
        else:
            response.close()
            return False, url, None

    def _download_stream_with_ffmpeg(self, url, filename):
        process = subprocess.Popen(
            ['ffmpeg', '-y', '-protocol_whitelist', 'file,blob,http,https,tcp,tls,crypto', '-i',
             url,
             '-c', 'copy',
             self.path / filename], stderr=subprocess.DEVNULL)
        return_code = process.wait(timeout=30 * 60)
        return return_code

    def _download_stream(self, l: Url) -> Tuple[bool, str, Optional[Path]]:
        """Downloads a stream with ffmpeg to the filesystem.

        :param l: A Url object to download.
        :return: A Tuple that describes the download (finished,url,path).
        """
        response = self.client.session.get(l.link)
        tree = html.fromstring(response.content.decode('utf-8'))
        video = tree.xpath('//*[not(self::head)]/*[@src and (@type or self::video) and not(self::script)]')[0]
        link = video.get('src')
        url = link
        link_path = Path(unquote(url))
        filename = iouuid.generate_id(self.path / link_path.name, rsuffix=rsuffix, size=2)
        return_code = self._download_stream_with_ffmpeg(url, filename)
        if return_code != 0 and not (self.path / filename).is_file():
            return_code = self._download_stream_with_ffmpeg(url, filename)  # try a second time if download fails.
        if return_code != 0:
            return False, l.link, None
        return True, l.link, self.path / filename
