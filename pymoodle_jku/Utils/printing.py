import platform
import subprocess

from pick import pick


def clean_screen():
    if platform.system() == 'Windows':
        subprocess.call('cls')
    else:
        subprocess.call('clear')


def print_courses(client):
    courses = client.courses()
    output = '\n'.join(map(lambda c: f'{c.id}: {c.fullname}', courses))
    print(output, flush=True)


def print_results_table(data, header, quiet=True):
    str_l = max(len(t) if isinstance(t, str) else len(t.fullname) for t in data.keys())
    str_r = max(len(t) for t in data.values())
    print(f'{header[0].ljust(str_l)} {header[1].ljust(str_r)}')
    if quiet:
        for c, v in data.items():
            print(f'{c.ljust(str_l)} {v.ljust(str_r)}')
        return None
    else:
        items = list(data.items())
        options = [f'{c.fullname.ljust(str_l)} {v.ljust(str_r)}' for c, v in items]
        options.append('Exit')
        option, index = pick(options)
        return None if index == len(items) else items[index][0]


def print_array_results_table(data, header):
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
