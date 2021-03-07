from typing import List

from examples.moodle_client import simple_client
from pymoodle_jku import Course, CourseData


# There are two way to load Courses
# First way is to send a request to moodle and get the Course list
# Problem is, if that's done we dont have the Course Page with all its info

# Second way is to load the Course List and then load to every course the course page
# PyMoodle handles that internally and only one param needs to be changed
# Problem: it will take longer

# Default is the second way.

def courses():
    # This will return a generator
    courses_generator = client.courses(load_pages=False)

    # to get a list of courses we wrap that in list
    courses: List[Course] = list(courses_generator)
    # print(courses)
    # As you can see course_page is empty

    courses_generator = client.courses()
    courses: List[Course] = list(courses_generator)
    # print(courses)
    # As you can see course_page is now loaded. But the whole method took more time.

    # If you first dont load the Moodle Page and do it later on you can insert the courses into courses()
    courses_generator = client.courses(load_pages=False)
    random_courses = list(courses_generator)[0:2]

    # You can now reload the
    courses = list(client.courses(load_pages=random_courses))

    # As client.courses() returns a generator you can simple iterate over it:
    # You will see that the courses aren't sorted if you run that multiple times
    # Thats because internally all requests will be done from multiple threads.
    # Thats also why there could be a delay between some prints
    for c in client.courses():
        print(c.fullname)
        # Check out the other attributes

    # The courses() method does also accept a filter expression.
    # Before all pages are loaded this can be run
    # For example, you want all Courses where there is the word "Logic", "KV", and "VL" in the fullname
    # The filter expression should return a bool.
    filter_words = ['Logic', 'KV', 'VL']

    # The parsing to tuple is done to make the object immutable.
    courses_generator = client.courses(filter_exp=lambda course, words=tuple(filter_words): any(
        word.lower() in course.fullname.lower() for word in words))

    print(list(courses_generator))


def course_page():
    course_list = list(client.courses())

    for course in course_list:
        # You can now parse a course_page to Course Data.
        # That will extract a lot of infos from the Page.
        course_data: CourseData = course.course_page.to_course_data()

        # A CourseData includes Links and Sections
        # Links are all available links on the page
        print(course_data.links)
        # With Links you can do much more. For example Download Stuff with the DownloadManager

        # A section is just a bunch of text from the moodle page
        print(course_data.sections)


if __name__ == '__main__':
    client = simple_client()
    courses()
    course_page()
