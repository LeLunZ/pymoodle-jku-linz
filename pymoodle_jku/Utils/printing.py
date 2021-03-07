import platform
import subprocess
from distutils.util import strtobool
from typing import Optional, Any, List

from pick import pick


def clean_screen():
    """
    Clears the terminal screen.
    :return:
    """
    if platform.system() == 'Windows':
        subprocess.call('cls')
    else:
        subprocess.call('clear')


def yn_question(question=''):
    """
    Converts a input to a boolean.
    :param question: A question to be asked while inputing.
    :return: returns the boolean representation of the string.
    """
    return strtobool(input(question).strip().lower())


def print_courses(client):
    """
    Loads and Prints all courses.
    :param client: A MoodleClient that is logged in.
    :return:
    """
    courses = client.courses()
    output = '\n'.join(map(lambda c: f'{c.id}: {c.fullname}', courses))
    print(output, flush=True)


def print_results_table(data, header, quiet=True) -> Optional[Any]:
    """
    Prints a interactive table.
    :param data: The data that should be printed.
    :param header: The header which should be printed.
    :param quiet: True when interactive mode should be off.
    :return: The picked value if interactive mode is on, else None
    """
    str_l = max(len(t) if isinstance(t, str) else len(t.fullname) for t in data.keys())
    str_r = max(len(t) for t in data.values())
    if quiet:
        print(f'{header[0].ljust(str_l)} {header[1].ljust(str_r)}')
        for c, v in data.items():
            print(f'{c.ljust(str_l)} {v.ljust(str_r)}')
        return None
    else:
        header_s = 'Press [Enter] to select a Course'
        items = list(data.items())
        options = [f'{c.fullname.ljust(str_l)} {v.ljust(str_r)}' for c, v in items]
        options.append('Exit')
        option, index = pick(options, title=header_s)
        return None if index == len(items) else items[index][0]


def print_array_results_table(data: List[List[str]], header: List[str]) -> None:
    """
    Prints a two dimenstional string array as table.
    :param data: Array that should be printed.
    :param header: The Headers that should be printed ontop of the data.
    :return:
    """
    cols = len(header)
    lengths = []
    reordered = list(zip(*data))
    splitline = '|'
    headerline = '|'
    for i in range(cols):
        str_l = max(len(t) for t in (reordered[i] + (header[i],)))
        lengths.append(str_l)
        headerline += f' {header[i].ljust(str_l)} |'
        splitline += '-' * (str_l + 2) + '|'
    print(splitline)
    print(headerline)
    print(splitline)
    for i in range(len(data)):
        print('|', end='')
        for j in range(len(data[i])):
            print(f' {data[i][j].ljust(lengths[j])}', end=' |')
        print()  # line break
    print(splitline)
