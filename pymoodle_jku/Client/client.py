import json
import subprocess
import time
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from io import BytesIO, StringIO
from tempfile import NamedTemporaryFile
from typing import Union, Generator

import requests
from requests import Response
from requests.adapters import HTTPAdapter

from requests_futures.sessions import FuturesSession
from lxml import html
from urllib3 import Retry
from pytube import YouTube

from pymoodle_jku.Classes.course import Course
from pymoodle_jku.Classes.course_data import UrlType, Url, CourseData


def requests_retry_session(
        retries=5,
        backoff_factor=0.3,
        session=None,
):
    session = session or requests.session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def requests_retry_session_async(
        retries=5,
        backoff_factor=0.3,
        session=None,
        executor=None
):
    session = session or FuturesSession(executor=executor)
    if type(session) is not FuturesSession:
        session = FuturesSession(session=session, executor=executor)
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class MoodleClient:
    def login(self, username, password):
        if username is None or password is None:
            raise ValueError
        self.session.cookies.clear()
        response = self.session.get('https://moodle.jku.at/jku/login/index.php')
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        url = response.url
        # session_id = url.split('jsessionid=')[1].split('?')[0]
        response = self.session.post(url, data={'j_username': username, 'j_password': password,
                                                '_eventId_proceed': 'Login'}, headers=headers)
        tree = html.fromstring(response.content.decode('utf-8'))
        form_action = tree.xpath('//form/@action')[0]
        form = tree.xpath('//form/div/input')
        data = {}
        for inp in form:
            name = inp.xpath('./@name')[0]
            value = inp.xpath('./@value')[0]
            data[name] = value
        response = self.session.post(form_action, data=data, headers=headers)
        response = self.session.get('https://moodle.jku.at/')
        content = response.content.decode('utf-8')
        index = content.find('sesskey')
        sesskey, count, qoute_count, sesskey_text = '', 0, 0, content[index:]
        while True:
            if sesskey_text[count] == '"':
                qoute_count += 1
            elif qoute_count == 2:
                sesskey += sesskey_text[count]
            if qoute_count == 3:
                break
            count += 1
        self.sesskey = sesskey
        cookies = self.session.cookies.get_dict()
        self.session.cookies.clear()
        self.session.cookies.set('MoodleSessionjkuSessionCookie', cookies['MoodleSessionjkuSessionCookie'])
        self.session.cookies.set(f'_shibsession_{cookies["shib_idp_session"]}', f'_{cookies["JSESSIONID"]}')
        return True

    def courses_overview(self) -> [Course]:
        headers = {'Content-type': 'application/json'}
        response = self.session.post(
            f'https://moodle.jku.at/jku/lib/ajax/service.php?sesskey={self.sesskey}&info=core_course_get_enrolled_courses_by_timeline_classification',
            data=json.dumps([{"index": 0, "methodname": "core_course_get_enrolled_courses_by_timeline_classification",
                              "args": {"offset": 0, "limit": 0, "classification": "all", "sort": "fullname",
                                       "customfieldname": "", "customfieldvalue": ""}}]), headers=headers)
        return [Course(*c.values()) for c in json.loads(response.content.decode('utf-8'))[0]['data']['courses']]

    def course_pure(self, url):
        response = self.session.get(url)
        tree = html.fromstring(response.content.decode('utf-8'))
        return tree.xpath('//body')[0]

    def urls_from_page(self, main_region):
        all_url_imgs = main_region.xpath('.//a/img')
        return [Url(i.getparent().xpath('./@href')[0],
                    UrlType[i.getparent().xpath('./@href')[0].split('/')[-2].capitalize()])
                for i in all_url_imgs]

    def course(self, url: Union[str, Course]) -> CourseData:
        body = self.course_pure(url)
        main_region = body.xpath('.//div[@id=$name]', name='region-main-box')[0]
        sections = main_region.xpath('.//ul[@class=$name]/li', name='topics')
        cd = CourseData(url if type(url) is Course else None, self.urls_from_page(main_region), sections)
        for l in cd.links:
            l.course = cd
        return cd

    def courses(self, urls: [str, Course]) -> Generator[Union[CourseData, None], None, None]:

        def processing(r, args, kwargs, course):
            tree = html.fromstring(r.content.decode('utf-8'))
            body = tree.xpath('//body')[0]
            main_region = body.xpath('.//div[@id=$name]', name='region-main-box')[0]
            sections = main_region.xpath('.//ul[@class=$name]/li', name='topics')
            all_url_imgs = main_region.xpath('.//a/img')
            urls = [Url(i.getparent().xpath('./@href')[0],
                        UrlType[i.getparent().xpath('./@href')[0].split('/')[-2].capitalize()])
                    for i in all_url_imgs]
            r.data = CourseData(course, urls, sections)
            for l in r.data.links:
                l.course = r.data

        futures = [
            self.future_session.get(url if type(url) is str else url.viewurl, timeout=5,
                                    hooks={'response': lambda r, *args, **kwargs: processing(r, args, kwargs,
                                                                                             url if type(
                                                                                                 url) is Course else None)})
            for
            url
            in urls]
        for cd in as_completed(futures):
            try:
                result = cd.result()
                yield result.data
            except Exception as e:
                # dont yield anything
                pass

    def _download_stream(self, l: Url):
        response = self.session.get(l.link)
        tree = html.fromstring(response.content.decode('utf-8'))
        video = tree.xpath('//*[not(self::head)]/*[@src and (@type or self::video) and not(self::script)]')[0]
        link = video.get('src')
        url = link
        tf = NamedTemporaryFile(suffix='.mp4')
        tf.close()
        process = subprocess.Popen(
            ['ffmpeg', '-protocol_whitelist', 'file,blob,http,https,tcp,tls,crypto', '-i',
             url,
             '-c', 'copy',
             tf.name])
        if process.poll() is None:  # just press y for the whole time to accept everything we get asked (secure? no.)
            process.communicate('y\n')
            process.communicate('y\n')
            process.communicate('y\n')
        return_code = process.wait(timeout=10 * 60)
        if return_code != 0:
            return None
            # or return False?
        time.sleep(0.5)
        with open(tf.name, 'rb') as fh:
            buf = BytesIO(fh.read())
            buf.name = Path(url).name
        Path(tf.name).unlink()  # Delete NamedTemporaryFile
        del tf
        return buf

    def _download(self, client, l):
        if l.type is UrlType.Resource:
            return client.get(l.link)
        elif l.type is UrlType.Folder:
            return client.post('https://moodle.jku.at/jku/mod/folder/download_folder.php',
                               data={'id': l.link.split('id=')[1].split('&')[0],
                                     'sesskey': self.sesskey})
        elif l.type is UrlType.Streamurl:
            if client is self.session:
                return self._download_stream(l)
            return self.future_session.executor.submit(self._download_stream, l)
        elif l.type is UrlType.Url:
            if client is self.session:
                return self._download_from_url(l)
            return self.future_session.executor.submit(self._download_from_url, l)
        else:
            return None

    def _save_response(self, resp: Response):
        try:
            data = resp.content.decode()
            file = StringIO(data)
        except (UnicodeDecodeError, AttributeError):
            file = BytesIO(resp.content)
        resp.close()
        return file

    def _download_from_url(self, l: Url):
        p = Path(l.link)
        link = l.link
        if '?' in p.name and '=' in p.name:  # doing this for moodle download
            link += '&forcedownload=1&redirect=1'  # normally every other server ignores this
        else:
            link += '?forcedownload=1&redirect=1'
        response = self.session.get(link, stream=True)
        if response.url.startswith('https://www.youtube.com/watch') or response.url.startswith(
                'youtube.com/watch') or response.url.startswith('https://youtube.com/watch'):
            youtube = YouTube(response.url)
            response.close()
            highest_res_stream = youtube.streams.filter(resolution='1080p', progressive=True, file_extension='mp4')
            if len(highest_res_stream) == 0:
                highest_res_stream = youtube.streams.filter(resolution='720p', progressive=True, file_extension='mp4')
                if len(highest_res_stream) == 0:
                    return None
            download_obj = highest_res_stream.order_by('fps')[-1]
            buffer = BytesIO()
            download_obj.stream_to_buffer(buffer=buffer)
            return buffer
        else:
            if (cnt_dis := response.headers.get('Content-Disposition')) is not None:
                filename = cnt_dis.split('filename="')[1][:-1]
                file = self._save_response(response)
                file.name = filename
                return file
            else:
                response.close()
                return None

    def download(self, data: Union[list, str, Url]) -> Union[list, Response, BytesIO, StringIO]:
        try:
            futures = [d for l in data if (d := self._download(self.future_session, l)) is not None]
            for d in as_completed(futures):
                yield d.result()
        except TypeError:
            if type(data) is Url:
                return self._download(self.session, data)
            else:
                return self._download(self.session, Url(data, UrlType.Url))

    def calendar(self, limit=26):
        url = f'https://moodle.jku.at/jku/lib/ajax/service.php?sesskey={self.sesskey}&info=core_calendar_get_action_events_by_timesort'
        data = [{"index": 0, "methodname": "core_calendar_get_action_events_by_timesort",
                 "args": {"limitnum": limit, "timesortfrom": int(time.time()), "limittononsuspendedevents": True}}]
        response = self.session.post(url, json=data)
        return response.json()

    @staticmethod
    def check_request(r, *args, **kwargs):
        if ('enroll' in r.url and 'enroll' not in r.request.url) or ('login' in r.url and 'login' not in r.request.url):
            raise Exception('Please login.')
        return r

    def __init__(self, pool_executor=ThreadPoolExecutor(max_workers=4), download_path=None):
        # limiting max_workers to 4 because of the large downloads
        self.session = requests_retry_session()
        self.download_path = download_path
        self.session.hooks['response'].append(self.check_request)
        self.future_session = requests_retry_session_async(session=self.session, executor=pool_executor)
        self.future_session.hooks['response'].append(self.check_request)
        self.sesskey = None
