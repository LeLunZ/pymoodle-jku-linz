import subprocess
import webbrowser

from sty import fg

from pymoodle_jku.utils.printing import print_pick_results_table, clean_screen


def main(all_parser):
    index = -2
    while index == -2:
        try:
            process = subprocess.Popen(['ffmpeg', '-h'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            return_code = process.wait(timeout=5)
            option, index = print_pick_results_table(
                [('config',), ('grades',), ('download',), ('timeline',), ('Overview',)], load_more=False)
            if index >= 0:
                clean_screen()
                all_parser[index].print_help()
        except FileNotFoundError:
            option, index = print_pick_results_table(
                [('Install FFmpeg and add it to the $PATH to download Videos from Moodle',), ('config',),
                 ('grades',),
                 ('download',), ('timeline',), ('Overview',), ], load_more=False)

            if index >= 1:
                index = index - 1
                clean_screen()
                all_parser[index].print_help()
            elif index == 0:
                webbrowser.open('https://ffmpeg.org/download.html')

    if index != -1:
        print('\n')
    print('To try out the different Utilities run one of these and follow the steps to log in:')
    print(fg.li_red + 'pymoodle grades' + fg.rs)
    print(fg.li_blue + 'pymoodle timeline' + fg.rs)
    print(fg.li_green + 'pymoodle download' + fg.rs)
