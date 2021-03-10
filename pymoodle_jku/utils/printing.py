import platform
import subprocess
from distutils.util import strtobool
from typing import Optional, Any, List

import readchar
from pick import Picker
from sty import fg


def print_exc(exception):
    print(fg.li_red + '\n\nPlease Notify LeLunZ on the JKU Discord Channel:' + fg.rs)
    print(str(exception))


def clean_screen():
    """
    Clears the terminal screen.
    :return:
    """
    if platform.system() == 'Windows':
        subprocess.call('cls', shell=True)
    else:
        subprocess.call('clear')


def yn_question(question=''):
    """
    Converts a char to a boolean.
    :param question: A question to be asked while inputing.
    :return: returns the boolean representation of the string.
    """
    print(question + ' (y/n): ', end='')
    return strtobool(readchar.readchar().lower())


def print_courses(client):
    """
    Loads and Prints all courses.
    :param client: A MoodleClient that is logged in.
    :return:
    """
    courses = client.courses()
    output = '\n'.join(map(lambda c: f'{c.id}: {c.fullname}', courses))
    print(output, flush=True)


def print_pick_results_table(data: List, multiselect=False, load_more=True) -> Optional[Any]:
    """
    Prints a interactive table.
    :param data: The data that should be printed.
    :param multiselect: True when multiple selection should be possible.
    :return: The picked value object.
    """
    lengths = []
    reordered = list(zip(*data))
    cols = len(reordered)
    for i in range(cols):
        str_l = max(len(t) for t in reordered[i])
        lengths.append(str_l)
    items = []
    for i in range(len(data)):
        line_out = f'{data[i][0].ljust(lengths[0])}'
        for j in range(1, len(data[i])):
            line_out += f' {data[i][j].ljust(lengths[j])}'
        items.append(line_out)

    if multiselect:
        header = 'Press [Space] to select and [Enter] to continue. [q] to exit.' + (
            ' [m] to load more from old semesters.' if load_more else '')
        picker = Picker(items, header, multiselect=True, min_selection_count=1)
    else:
        header = 'Press [Enter] to continue. [q] to exit.' + (
            ' Press [m] to load more from old semesters.' if load_more else '')
        picker = Picker(items, header)

    def return_exit(_):
        return None, -1

    def return_load(_):
        return None, -2

    picker.register_custom_handler(ord('q'), return_exit)
    picker.register_custom_handler(ord('Q'), return_exit)
    picker.register_custom_handler(ord('m'), return_load)
    picker.register_custom_handler(ord('M'), return_load)

    if multiselect:
        selected = picker.start()
        return selected
    else:
        option, index = picker.start()
        return option, index


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
