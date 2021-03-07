import unittest
from pathlib import Path

import keyring

from pymoodle_jku.Classes.course import Course
from pymoodle_jku.Classes.course_data import CourseData
from pymoodle_jku.Client.client import MoodleClient


# If you want to suppress the ResourceWarnings uncomment this:
# import warnings
# warnings.filterwarnings("ignore", category=ResourceWarning)
# These warnings are an indication that everything is working correctly and nothing is going wrong.


class TestPyMoodleClientLogin(unittest.TestCase):
    def setUp(self):
        self.client = MoodleClient()
        pymoodle_conf = Path.home() / '.pymoodle'
        if not pymoodle_conf.is_file():
            username = input('username: ')
            password = input('password: ')
            pymoodle_conf.write_text(username)
            keyring.set_password('pymoodle-jku', username, password)

    def test_login(self):
        pymoodle_conf = Path.home() / '.pymoodle'
        if pymoodle_conf.is_file():
            username = pymoodle_conf.read_text().strip()
            password = keyring.get_password('pymoodle-jku', username)
        else:
            return self.fail('Please setup pymoodle login credentials')
        auth = False
        count = 0
        while not auth:
            if count > 5:
                return self.fail('more than 5 login tries failed.')
            try:
                auth = self.client.login(username, password)
                count += 1
            except Exception:
                print('Login failed, trying again...')


class TestPyMoodleClient(unittest.TestCase):
    def setUp(self):
        self.client = MoodleClient()
        pymoodle_conf = Path.home() / '.pymoodle'
        username = pymoodle_conf.read_text().strip()
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

    def test_calendar(self):
        pass

    def test_valuation_overview(self):
        overview = self.client.valuation_overview()
        self.assertIs(type(overview), dict)

    def test_detailed_valuation(self):
        valuation_generator = self.client.multi_valuation()

        self.assertGreater(len(list(valuation_generator)), 0)


if __name__ == '__main__':
    unittest.main()
