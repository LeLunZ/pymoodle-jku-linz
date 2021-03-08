import unittest
from pathlib import Path

import keyring

from pymoodle_jku.Classes.course_data import Url, UrlType
from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Client.download_manager import DownloadManager
from pymoodle_jku.Utils.config import config


class TestDownloadManager(unittest.TestCase):
    def setUp(self):
        self.client = MoodleClient()
        self.download_path = Path('./downloadTest')
        username = config['Username']
        password = keyring.get_password('pymoodle-jku', username)
        self.client.login(username, password)

        try:
            self.download_path.mkdir()
        except (FileNotFoundError, OSError):
            pass

    def test_simple_download(self):
        fail_download = Url('https://test.com/afs', UrlType.Streamurl)  # some random url without video
        dm = DownloadManager([fail_download], self.client, self.download_path)
        dm.download()
        self.assertGreater(len(dm.failed), 0)

        # some m3u8 testing sites
        working_download = Url('http://demo.unified-streaming.com/video/tears-of-steel/tears-of-steel.ism/.m3u8',
                               UrlType.Streamurl)  # some random url without video
        working_download_2 = Url(
            'https://multiplatform-f.akamaihd.net/i/multi/will/bunny/big_buck_bunny_,640x360_400,640x360_700,640x360_1000,950x540_1500,.f4v.csmil/master.m3u8',
            UrlType.Streamurl)
        working_download_3 = Url(
            'https://devimages.apple.com.edgekey.net/iphone/samples/bipbop/bipbopall.m3u8',
            UrlType.Streamurl)
        working_download_4 = Url(
            'https://devimages.apple.com.edgekey.net/iphone/samples/bipbop/bipbopall.m3u8',
            UrlType.Streamurl)
        working_download_5 = Url(
            'https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8',
            UrlType.Streamurl)
        dm = DownloadManager(
            [working_download, working_download_5, working_download_4, working_download_2, working_download_3],
            self.client, self.download_path)
        dm.download()
        self.assertGreater(len(dm.done), 0)

        for url, path in dm.done:
            self.assertTrue(path.is_file())
            path.unlink()

    def test_moodle_download(self):
        courses = self.client.courses()

        counter = 0
        for c in courses:
            if 'Logic' in c.fullname:
                continue  # that's something you dont want to download
            if counter > 1:
                break  # test only 2 courses
            valuation = self.client.single_valuation(c)
            links = c.course_page.to_course_data().links

            downloads = valuation + links

            dm = DownloadManager(downloads,
                                 self.client, self.download_path)
            dm.download()
            self.assertGreater(len(dm.done), 0)

            for url, path in dm.done:
                self.assertTrue(path.is_file())
                path.unlink()

        del courses

    def tearDown(self) -> None:
        urls = self.download_path / 'urls.txt'
        if urls.is_file():
            urls.unlink()
        self.download_path.unlink()


if __name__ == '__main__':
    unittest.main()
