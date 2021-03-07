from pathlib import Path

from examples.moodle_client import simple_client
from pymoodle_jku.Client.download_manager import DownloadManager


def download():
    # Pages must be loaded when downloading, so load_pages must be True (default).
    courses = client.courses()

    test_dir = Path('./downloadTest')
    try:
        test_dir.mkdir()
    except:
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


if __name__ == '__main__':
    client = simple_client()
    download()
