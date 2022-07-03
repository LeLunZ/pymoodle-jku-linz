from pathlib import Path

from examples.moodle_client import simple_client
from pymoodle_jku.classes.course_data import CourseData, UrlType
from pymoodle_jku.client.download_manager import DownloadManager


def download():
    # Pages must be loaded when downloading, so load_pages must be True (default).
    courses = client.courses()

    test_dir = Path('./downloadTest')
    try:
        test_dir.mkdir()
    except (FileNotFoundError, OSError):
        pass

    for c in courses:
        # To download all links we load them from the course
        links = c.course_page.to_course_data().links

        # To download all evaluations we also load them
        valuations = client.single_valuation(c)

        downloads = links + valuations

        # Create a Download Manager with the downloads, client and directory
        dm = DownloadManager(downloads, client, test_dir)

        # DOWNLOAD TODO Uncomment this to download
        # dm.download()

        for url, file in dm.done:
            print(f'{url} is located at {file}')

        for url in dm.failed:
            print(f'{url} failed.')


def _check():
    courses = client.courses()
    not_implemented = {}
    for course in courses:
        # You can now parse a course_page to Course Data.
        # That will extract a lot of infos from the Page.
        course_data: CourseData = course.course_page.to_course_data()

        for l in course_data.links:
            if l.type is UrlType.Quiz:
                continue
            elif l.type is UrlType.Resource:
                continue
            elif l.type is UrlType.Folder:
                continue
            elif l.type is UrlType.Streamurl:
                continue
            elif l.type is UrlType.Url:
                continue
            else:
                not_implemented[l.type] = l.link

    print(not_implemented)
    print(not_implemented.keys())
    print(not_implemented.values())


if __name__ == '__main__':
    client = simple_client()
    #download()
    _check()
