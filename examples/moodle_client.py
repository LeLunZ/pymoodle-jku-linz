from concurrent.futures.thread import ThreadPoolExecutor

from pymoodle_jku import MoodleClient


def simple_client():
    user = input('Username: ')
    passwd = input('Password: ')

    simple_moodle_client = MoodleClient()
    simple_moodle_client.login(user, passwd)  # Exceptions could be raised if user/password are wrong.
    return simple_moodle_client


def client_with_more_threads():
    user = input('Username: ')
    passwd = input('Password: ')

    # You can also parse a bigger ThreadPoolExecutor
    moodle_client = MoodleClient(pool_executor=ThreadPoolExecutor(max_workers=8))
    moodle_client.login(user, passwd)  # Exceptions could be raised if user/password are wrong.
    return moodle_client
