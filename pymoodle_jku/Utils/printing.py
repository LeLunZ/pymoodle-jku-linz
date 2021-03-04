import platform
import subprocess

from pick import pick


def clean_screen():
    if platform.system() == 'Windows':
        subprocess.call('cls')
    else:
        print(chr(27) + "[2J")


def print_courses(client):
    courses = client.courses()
    output = '\n'.join(map(lambda c: f'{c.id}: {c.fullname}', courses))
    print(output, flush=True)


def print_results_table(data, header, quiet=True):
    str_l = max(len(t) if type(t) is str else len(t.fullname) for t in data.keys())
    str_r = max(len(t) for t in data.values())
    print(f'{header[0].ljust(str_l)} {header[1].ljust(str_r)}')
    if quiet:
        for c, v in data.items():
            print(f'{c.ljust(str_l)} {v.ljust(str_r)}')
        return None
    else:
        items = data.items()
        options = [f'{c.fullname.ljust(str_l)} {v.ljust(str_r)}' for c, v in items]
        options.append('Exit')
        option, index = pick(options)
        return None if index == len(items) else items[index][0]
