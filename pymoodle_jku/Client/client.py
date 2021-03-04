import json
import time
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Union, List

import requests
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession
from urllib3 import Retry

from pymoodle_jku.Classes.course import Course
from pymoodle_jku.Classes.evaluation import Evaluation
from pymoodle_jku.Utils.moodle_html_parser import LoginPage, MyPage, \
    ValuationOverviewPage, CoursePage, ValuationPage


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

        # parsing Login page
        l_page = LoginPage.from_response(response)
        response = self.session.post(l_page.action, data=l_page.data, headers=headers)

        response = self.session.get('https://moodle.jku.at/')
        m_page = MyPage.from_response(response)

        self.sesskey, self.userid = m_page.sesskey, m_page.userid
        cookies = self.session.cookies.get_dict()
        self.session.cookies.clear()
        self.session.cookies.set('MoodleSessionjkuSessionCookie', cookies['MoodleSessionjkuSessionCookie'])
        self.session.cookies.set(f'_shibsession_{cookies["shib_idp_session"]}', f'_{cookies["JSESSIONID"]}')
        return True

    def valuation_overview(self) -> dict:
        response = self.session.get('https://moodle.jku.at/jku/grade/report/overview/index.php')
        v_page = ValuationOverviewPage(response)
        return v_page.valuation

    def single_valuation_overview(self, course: Union[Course, list]) -> List[Evaluation]:
        course_id = course.id
        response = self.session.get(
            f'https://moodle.jku.at/jku/course/user.php?mode=grade&id={course_id}&user={self.userid}')
        v_page = ValuationPage(response)
        return v_page.evaluations()

    def multi_valuation_overview(self, courses: List[Course] = None):

        def build_valuation(r, c):
            r.data = (c, ValuationPage(r).evaluations())

        if courses is None:
            courses = list(self.courses(load_page=False))
            print(courses)

        futures = [self.future_session.get(
            f'https://moodle.jku.at/jku/course/user.php?mode=grade&id={course.id}&user={self.userid}', timeout=5,
            hooks={'response': lambda r, c=course, *args, **kwargs: build_valuation(r, c)}) for
            course in courses]

        for f in as_completed(futures):
            try:
                result = f.result()
                yield result.data
            except Exception as e:
                # dont yield anything
                pass

    def courses(self, load_page=True, filter_ids=None) -> List[Course]:
        headers = {'Content-type': 'application/json'}
        response = self.session.post(
            f'https://moodle.jku.at/jku/lib/ajax/service.php?sesskey={self.sesskey}&info=core_course_get_enrolled_courses_by_timeline_classification',
            data=json.dumps([{"index": 0, "methodname": "core_course_get_enrolled_courses_by_timeline_classification",
                              "args": {"offset": 0, "limit": 0, "classification": "all", "sort": "fullname",
                                       "customfieldname": "", "customfieldvalue": ""}}]), headers=headers)

        courses_json = json.loads(response.content.decode('utf-8'))[0]['data']['courses']

        if filter_ids is not None:
            to_download = []
            for e in courses_json:
                if int(e['id']) in filter_ids:
                    to_download.append(e)
            courses_json = to_download

        if load_page is False:
            for c in courses_json:
                yield Course(**c)

            return

        def build_course(r, c):
            course = Course(**c, course_page=CoursePage(r))
            r.data = course

        futures = [self.future_session.get(c['viewurl'], timeout=5,
                                           hooks={'response': lambda r, c=c, *args, **kwargs: build_course(r, c)})
                   for c in courses_json]

        for f in as_completed(futures):
            try:
                result = f.result()
                yield result.data
            except Exception as e:
                # dont yield anything
                pass

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
        self.session = requests_retry_session()
        self.download_path = download_path
        self.session.hooks['response'].append(self.check_request)
        self.future_session = requests_retry_session_async(session=self.session, executor=pool_executor)
        self.future_session.hooks['response'].append(self.check_request)
        self.sesskey = None
        self.userid = None
