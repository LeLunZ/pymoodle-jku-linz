import re
import subprocess
import time
import traceback
from concurrent.futures import as_completed
from pathlib import Path
from urllib.parse import unquote, urlparse

import iouuid
from lxml import html
from pytube import YouTube

from pymoodle_jku.Classes.course_data import UrlType, Url
from pymoodle_jku.Classes.evaluation import Evaluation
from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Utils.moodle_html_parser import QuizSummary, QuizPage


def rsuffix(suffix):
    if suffix.startswith('.m3u8') or suffix.startswith('.m3u'):
        return '.mp4'
    else:
        return suffix


class DownloadManager:
    def __init__(self, urls, client: 'MoodleClient', path):
        self.urls = urls
        self.failed = []
        self.done = []
        self.client = client
        self.path = Path(path)

    def get_request(self, url):
        response = self.client.session.get(url, stream=True)
        return self.process_response(url, response)

    def post_request(self, url):
        response = self.client.session.post('https://moodle.jku.at/jku/mod/folder/download_folder.php',
                                            data={'id': url.split('id=')[1].split('&')[0],
                                                  'sesskey': self.client.sesskey}, stream=True)
        return self.process_response(url, response)

    def download_evaluation(self, l):
        response = self.client.session.get(l.url)
        q_page = QuizSummary(response)
        u = q_page.quiz_url()
        if u is None:
            return False, l.url, None

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
            except:
                pass

            for i in images:
                response = self.client.session.get(str(i), stream=True)
                link, done, file = self.process_response(str(i), response, path=d_path)
                if file is not None:
                    output = output.replace(i, str(file.relative_to(self.path)))

        filename = iouuid.generate_id(self.path / f'{name}.md', size=2)

        with open(self.path / filename, 'w') as f:
            f.write(output)
        # HTML(string=html_str.decode('utf-8')).write_pdf(filename)

        # pdfkit.from_string(html_str.decode('utf-8'), filename)

        return True, l.url, self.path / filename

        # return self.process_response(url, response)

    def _download(self, l):
        if type(l) is Evaluation or l.type is UrlType.Quiz:
            return self.client.future_session.executor.submit(self.download_evaluation, l)
        if l.type is UrlType.Resource:
            return self.client.future_session.executor.submit(self.get_request, l.link)
        elif l.type is UrlType.Folder:
            return self.client.future_session.executor.submit(self.post_request, l.link)
        elif l.type is UrlType.Streamurl:
            return self.client.future_session.executor.submit(self._download_stream, l)
        elif l.type is UrlType.Url:
            return self.client.future_session.executor.submit(self.download_from_url, l)
        else:
            # return false because if we later add the datatype we still want to download it.
            def return_false(l):
                return False, l.link, None

            return self.client.future_session.executor.submit(return_false, l)

    def download(self):
        futures = [d for l in self.urls if (d := self._download(l)) is not None]
        for f in as_completed(futures):
            try:
                done, url, file = f.result()
                if done:
                    self.done.append((url, file))
                else:
                    self.failed.append(url)
            except Exception as err:
                print(str(err))
                traceback.print_exc()

    def download_from_url(self, url):
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
            download_obj.download(output_path=self.path, filename=filename)
            return True, url, self.path / filename
        else:
            return self.process_response(url, response)

    def process_response(self, url, response, path=None):
        if (cnt_dis := response.headers.get('Content-Disposition')) is not None:
            filename = cnt_dis.split('filename="')[1][:-1]
            size = 1024 * 1024 * 20
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

    def _download_stream(self, l: Url):
        response = self.client.session.get(l.link)
        tree = html.fromstring(response.content.decode('utf-8'))
        video = tree.xpath('//*[not(self::head)]/*[@src and (@type or self::video) and not(self::script)]')[0]
        link = video.get('src')
        url = link
        filename = iouuid.generate_id(self.path / Path(unquote(url)).name, rsuffix=rsuffix, size=2)
        process = subprocess.Popen(
            ['ffmpeg', '-protocol_whitelist', 'file,blob,http,https,tcp,tls,crypto', '-i',
             url,
             '-c', 'copy',
             self.path / filename])
        if process.poll() is None:  # just press y for the whole time to accept everything we get asked (secure? no.)
            process.communicate('y\n')
            process.communicate('y\n')
            process.communicate('y\n')
        return_code = process.wait(timeout=30 * 60)
        if return_code != 0:
            return False, l.link, None
        time.sleep(0.5)
        return True, l.link, self.path / filename
