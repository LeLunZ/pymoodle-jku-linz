import unittest
from getpass import getpass
from pathlib import Path

import keyring

from pymoodle_jku.Classes.course import Course
from pymoodle_jku.Classes.course_data import CourseData, Url, UrlType
from pymoodle_jku.Client.client import MoodleClient

# If you want to suppress the ResourceWarnings uncomment this:
# import warnings
# warnings.filterwarnings("ignore", category=ResourceWarning)
# These warnings are an indication that everything is working correctly and nothing is going wrong.
from pymoodle_jku.Client.download_manager import DownloadManager
from pymoodle_jku.Utils.config import config, set_new_user


class TestPyMoodleClientLogin(unittest.TestCase):
    def setUp(self):
        # setting up environment
        self.client = MoodleClient()
        if (username := config['Username']) is None:
            username = input('username: ')
        password = keyring.get_password('pymoodle-jku', username)
        if password is None:
            password = getpass()
            set_new_user((username, password))

    def test_login(self):
        auth = False
        count = 0
        while not auth:
            if count > 5:
                return self.fail('more than 5 login tries failed.')
            try:
                password = keyring.get_password('pymoodle-jku', config['Username'])
                auth = self.client.login(username=config['Username'], password=password)
            except Exception as err:
                count += 1
                print('Login failed, trying again...')


class TestPyMoodleClient(unittest.TestCase):
    def setUp(self):
        self.client = MoodleClient()
        username = config['Username']
        password = keyring.get_password('pymoodle-jku', username)
        self.client.login(username, password)

    def test_courses_without_page(self):
        courses = self.client.courses(load_pages=False)
        all_courses = []
        for c in courses:
            # check if course is duplicated
            for co in all_courses:
                self.assertNotEqual(c.fullname, co.fullname)

            all_courses.append(c)
            self.assertIs(type(c), Course)

        self.assertGreater(len(all_courses), 0)

    def test_courses(self):
        courses_generator = self.client.courses()
        all_courses = []
        for c in courses_generator:

            # check if course is duplicated
            for co in all_courses:
                self.assertNotEqual(c.fullname, co.fullname)
                self.assertNotEqual(c.course_page, co.course_page)

            all_courses.append(c)

            self.assertIs(type(c), Course)
            self.assertIsNotNone(c.course_page)

            # check if course is parsable to data
            self.assertIs(type(c.course_page.to_course_data()), CourseData)

        self.assertGreater(len(all_courses), 0)

    def test_courses_reload_page(self):
        courses = list(self.client.courses(load_pages=False))
        courses_2 = list(self.client.courses(load_pages=courses))

        for c in courses_2:
            course = next(c_2 for c_2 in courses if c.id == c_2.id)
            self.assertIs(c, course)
            self.assertIsNotNone(c.course_page)

    def test_courses_filter(self):
        courses_generator = self.client.courses(load_pages=False, filter_exp=lambda c: 'VL' in c.fullname)
        for c in courses_generator:
            self.assertTrue('VL' in c.fullname)

    def test_calendar(self):
        calendar_events = self.client.calendar()
        for t in calendar_events:
            # Testing for some basics
            self.assertIsNotNone(t)
            self.assertIsNotNone(t.id)
            self.assertIsNotNone(t.course_id)
            self.assertIsNotNone(t.name)
            self.assertIsNotNone(t.timestart)

    def test_valuation_overview(self):
        overview = self.client.valuation_overview()
        self.assertIs(type(overview), dict)

    def test_detailed_single_valuation(self):
        courses = list(self.client.courses(load_pages=False))
        to_load = courses[0]
        valuation_generator = list(self.client.single_valuation(to_load))

        self.assertIsNotNone(valuation_generator)

    def test_detailed_multi_valuation(self):
        valuation_generator = self.client.multi_valuation()

        vals = list(valuation_generator)
        self.assertGreater(len(vals), 0)

        for course, val in valuation_generator:
            self.assertIs(type(val), list)


class TestDownloadManager(unittest.TestCase):
    def setUp(self):
        self.client = MoodleClient()
        self.download_path = Path('./downloadTest')
        username = config['Username']
        password = keyring.get_password('pymoodle-jku', username)
        self.client.login(username, password)

        try:
            self.download_path.mkdir()
        except:
            pass

    def test_simple_download(self):
        fail_download = Url('https://test.com/afs', UrlType.Streamurl)  # some random url without video
        dm = DownloadManager([fail_download], self.client, self.download_path)
        dm.download()

        self.assertGreater(len(dm.failed), 0)


if __name__ == '__main__':
    unittest.main()
