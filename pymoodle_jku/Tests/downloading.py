import asyncio
import json
import subprocess
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

from pymoodle_jku.Classes.course_data import UrlType, Url
from pymoodle_jku.Client.client import MoodleClient

if __name__ == "__main__":
    links_dict = {}
    # download everything you can
    client = MoodleClient()
    client.login(input('username: '), input('password:'))
    cal = client.calendar()
    stream = client._download_stream(Url('https://moodle.jku.at/jku/mod/streamurl/view.php?id=4431710', UrlType.Streamurl))
    res = client.download(Url('https://moodle.jku.at/jku/pluginfile.php/4849684/mod_resource/content/1/IMG_20201026_194952.jpg', UrlType.Url))
    courses = client.courses_overview()
    for c in client.courses(courses):
        for l in c.links:
            links_dict[l.type] = l
    temp_dir = Path('./temp')
    try:
        temp_dir.mkdir()
    except:
        pass
    for l in client.download(links_dict.values()):
        print(l.result().content)
        try:
            data = l.result().content.decode()
        except (UnicodeDecodeError, AttributeError):
            #
            pass
    for l in links_dict.values():
        # download
        response = client.session.get(l.link)
        try:
            filename = response.headers.get('Content-Disposition').split('filename="')[1][:-1]
        except Exception as e:
            print(e)
            continue
        print(filename)
        if Path(filename).is_file():
            continue
        with open(temp_dir / filename, 'wb') as f:
            f.write(response.content)
        pass
    pass