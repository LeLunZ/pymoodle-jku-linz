import json
import time
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Union, List, Callable, Tuple, Generator, Iterator, Optional, Type

import requests
from requests.adapters import HTTPAdapter
from requests_futures.sessions import FuturesSession
from urllib3 import Retry

from pymoodle_jku.classes.course import Course
from pymoodle_jku.classes.evaluation import Evaluation
from pymoodle_jku.classes.events import Event
from pymoodle_jku.classes.exceptions import NotLoggedInError, LoginError
from pymoodle_jku.client.html_parser import LoginPage, MyPage, \
    ValuationOverviewPage, CoursePage, ValuationPage
from pymoodle_jku.utils.printing import print_exc


def requests_retry_session(
        retries=5,
        backoff_factor=0.3,
        session=None,
) -> requests.session:
    """
    Creates or modifies a session object for retrying requests if they fail.
    :param retries: How often a Retry should be done
    :param backoff_factor: Look at the official Requests documentation
    :param session: A session object, if not given one will be created.
    :return: The given or new session object.
    """
    session = session or requests.session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=100, pool_connections=20)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def requests_retry_session_async(
        retries=5,
        backoff_factor=0.3,
        session=None,
        executor=None
) -> FuturesSession:
    """
    Creates or modifies a FutureSession Object.

    :param retries: How often a Retry should be done
    :param backoff_factor: Look at the official Requests documentation
    :param session: A session object, if not given one will be created.
    :param executor: A ThreadPoolExecutor for the new session if no session is given.
    :return: The given or new session object.
    """
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
    def login_with_old_session(self, cookies, sesskey, userid):
        """Tries old cookies and sesskey.
        """
        self.session.cookies.clear()
        self.sesskey = sesskey
        self.userid = userid
        self.session.cookies.update(cookies)

    def clear_client(self):
        self.sesskey = None
        self.userid = None
        self.session.cookies.clear()

    def login(self, username, password) -> bool:
        """Retrieves tokens and cookies for moodle.

        :param username: Official JKU Username
        :param password: Official JKU Password
        :return: True if Login worked.
        :raises Exception: if Login doesn't work.
        """
        if username is None or password is None:
            raise LoginError('Provide Username or Password')
        try:
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
        except (NotLoggedInError, IndexError, KeyError):
            return False
        return True

    def valuation_overview(self) -> dict:
        """Loads the Overview of all valuations from Moodle.

        :return: Dict[int, (str, str)]: course_id, name, Points
        """
        response = self.session.get('https://moodle.jku.at/jku/grade/report/overview/index.php')
        v_page = ValuationOverviewPage(response)
        return v_page.valuation

    def single_valuation(self, course: Course) -> List[Evaluation]:
        """Returns a List of Evaluation Objects for the given Course.
        CoursePage not required.

        :param course: Course Object for which the Evaluation should be loaded.
        :return:
        """
        course_id = course.id
        response = self.session.get(
            f'https://moodle.jku.at/jku/course/user.php?mode=grade&id={course_id}&user={self.userid}')
        v_page = ValuationPage(response)
        return v_page.evaluations()

    def multi_valuation(self, courses: Optional[Union[List[Course], Iterator[Course]]] = None) -> Generator[
        Tuple[Course, List[Evaluation]], None, None]:
        """Returns a List of Tuples with each Course and the corresponding evaluations.
        CoursePage not required.

        :param courses: A List of courses to load the evaluation from. Course.course_page doesn't need to be loaded.
        :return: Generator[Tuple[Course, List[Evaluation]]] The Course is the same Object as the input and doesn't change.
        """

        def build_valuation(r, c):
            r.data = (c, ValuationPage(r).evaluations())

        if courses is None:
            courses = list(self.courses(load_pages=False))

        futures = [self.future_session.get(
            f'https://moodle.jku.at/jku/course/user.php?mode=grade&id={course.id}&user={self.userid}', timeout=5,
            hooks={'response': lambda r, c=course, *args, **kwargs: build_valuation(r, c)}) for
            course in courses]

        for f in as_completed(futures):
            try:
                result = f.result()
                yield result.data
            except (SystemExit, KeyboardInterrupt, GeneratorExit):
                raise
            except Exception as e:
                print_exc(e)

    def courses(self, load_pages: Union[bool, List[Course]] = True, filter_exp: Callable[[Course], bool] = None) -> \
            Generator[Course, None, None]:
        """Loads all the moodle Courses.

        :param load_pages: If True the course.course_page will be loaded. This takes more time, as each page needs to
        be loaded individually. If load_pages is set to a List of Courses, only the course_page's will be loaded.
        :param filter_exp: If not None, the filter will be applied to filter the Courses.
        This speeds up Page loading.
        :return: Returns a Generator for all (filtered) Courses.
        """
        if type(load_pages) is list:
            courses_json = load_pages
        else:
            headers = {'Content-type': 'application/json'}
            response = self.session.post(
                f'https://moodle.jku.at/jku/lib/ajax/service.php?sesskey={self.sesskey}',
                data=json.dumps(
                    [{"index": 0, "methodname": "core_course_get_enrolled_courses_by_timeline_classification",
                      "args": {"offset": 0, "limit": 0, "classification": "all", "sort": "fullname"}},
                     {"index": 1, "methodname": "core_course_get_enrolled_courses_by_timeline_classification",
                      "args": {"offset": 0, "limit": 0, "classification": "hidden", "sort": "fullname"}}]),
                headers=headers)

            courses_json = json.loads(response.content.decode('utf-8'))[0]['data']['courses'] + \
                           json.loads(response.content.decode('utf-8'))[1]['data']['courses']

            if load_pages is False:
                for c in courses_json:
                    co = Course(**c)
                    if filter_exp is not None and filter_exp(co):
                        yield co
                    elif filter_exp is None:
                        yield co
                return
            else:
                courses_json = [Course(**c) for c in courses_json]

        if filter_exp is not None:
            courses_json = filter(filter_exp, courses_json)

        def build_course(r, c):
            c.course_page = CoursePage(r)
            r.data = c

        futures = [self.future_session.get(c.viewurl, timeout=5,
                                           hooks={'response': lambda r, c=c, *args, **kwargs: build_course(r, c)})
                   for c in courses_json]

        for f in as_completed(futures):
            try:
                result = f.result()
                yield result.data
            except (SystemExit, KeyboardInterrupt, GeneratorExit):
                raise
            except Exception as e:
                print_exc(e)

    def calendar(self, limit=26) -> List[Event]:
        """Gets the calendar entries. (Assignments, Exams etc.)

        :param limit: Max amount of entries to load.
        :return: A List of Calendar Events.
        """
        url = f'https://moodle.jku.at/jku/lib/ajax/service.php?sesskey={self.sesskey}'
        data = [{"index": 0, "methodname": "core_calendar_get_action_events_by_timesort",
                 "args": {"limitnum": limit, "timesortfrom": int(time.time()), "limittononsuspendedevents": True}}]
        response = self.session.post(url, json=data)

        events = []
        for o in response.json()[0]['data']['events']:
            event = Event(
                o['id'],
                o['name'],
                o['description'],
                o['modulename'],
                o['eventtype'],
                o['timestart'],
                o['timesort'],
                o['course']['fullname'],
                o['course']['id'],
                o['url'])
            events.append(event)
        return events

    @staticmethod
    def check_request(r, *args, **kwargs):
        """Takes a response object and checks if the user is logged in. If keywords like 'login' or 'enroll' are
        found in the url, the user seems to be logged out.

        :param r: Response that should be checked for logout.
        :param args:
        :param kwargs:
        :return: returns the response.

        :raises Exception: If user isn't logged in.
        """
        if (r.headers.get('Content-Type') == 'application/json; charset=utf-8' or r.headers.get(
                'Content-Type') == 'application/json') and 'moodle.jku.at' in r.url:
            j = r.json()
            if type(j) is list and type(j[0]) is dict and 'error' in j[0] and j[0]['error'] is True:
                raise NotLoggedInError('Please Login')
        else:
            if '<a href="https://moodle.jku.at/jku/login/index.php">' in r.text and r.is_redirect:
                raise NotLoggedInError('Please Login')
            if '<title>jku: Dashboard (GUEST)</title>' in r.text:
                raise NotLoggedInError('Please login.')

        def check_url(url, redirect_url, redirect):
            if ('enroll' in redirect_url and (('enroll' not in url) or redirect)) or (
                    'login' in redirect_url and (('login' not in url) or redirect)):
                raise NotLoggedInError('Please login.')

        # check_url(r.request.url, r.url, r.is_redirect)
        # for h in r.history:
        #    check_url(r.request.url, h.url, h.is_redirect)
        return r

    def __init__(self, pool_executor=ThreadPoolExecutor(max_workers=4)):
        """Initializes a MoodleClient, a client can load Data from Moodle.

        :param pool_executor: A instance of a ThreadPoolExecutor.
        """
        self.session = requests_retry_session()
        self.session.hooks['response'].append(self.check_request)
        self.future_session = requests_retry_session_async(session=self.session, executor=pool_executor)
        self.future_session.hooks['response'].append(self.check_request)
        self.sesskey = None
        self.userid = None
