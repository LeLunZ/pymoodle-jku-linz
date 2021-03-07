from typing import List

from examples.moodle_client import simple_client
from pymoodle_jku import Course, CourseData
from pymoodle_jku import Evaluation


def valuation_overview():
    # The Valuation Overview will just return a dictionary
    # the key is the name of the subject, the value is the score.
    # This is parsed from this page https://moodle.jku.at/jku/grade/report/overview/index.php
    overview = client.valuation_overview()

    for subject, score in overview:
        print(f'{score}     {subject}')


def in_depth_valuation():
    # To get a deeper valuation you fist need the course
    # This course doesn't need a course_page
    course_list = list(client.courses(load_pages=False))

    single_course = course_list[0]

    # To get a single evaluation list you can do this:
    evaluations: List[Evaluation] = client.single_valuation(single_course)
    # This is a list with all evaluations from one course
    # A single evaluation includes
    print(evaluations[0].name)
    print(evaluations[0].type)
    print(evaluations[0].grade)
    print(evaluations[0].grade_range)
    print(evaluations[0].url)

    # To get multiple evaluations
    course_evaluations_generator = client.multi_valuation(course_list)
    # This is a generator of multiple evaluations

    # Every generation returns the course and the valuation.
    for course, evaluations in course_evaluations_generator:
        print(course.fullname)
        for eva in evaluations:
            print(eva.name, end=' ')
            print(eva.type, end=' ')
            print(eva.grade, end=' ')
            print(eva.grade_range, end=' ')
            print(eva.url)


if __name__ == '__main__':
    client = simple_client()
    valuation_overview()
    in_depth_valuation()
