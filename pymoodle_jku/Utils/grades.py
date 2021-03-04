from argparse import Namespace

from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Utils.printing import print_results_table, clean_screen


def main(client: MoodleClient, args: Namespace):
    valuations = client.valuation_overview()
    if args.quiet:
        print_results_table(valuations, ['Course', 'Points'])
    else:
        courses = client.courses(load_page=False)
        vals = {}
        for c in courses:
            if c.fullname in valuations.keys():
                vals[c] = valuations[c.fullname]
        while True:
            course = print_results_table(vals, ['Course', 'Points'], quiet=False)
            clean_screen()
            if course is None:
                exit(0)
            else:
                evaluations = client.single_valuation_overview(course)
                print_results_table([(f'{e.name}', f'{e.grade}') for e in evaluations], ['Name', 'Points'], quiet=True)
                enter_press = input('\nPress Enter to continue')
                clean_screen()
            pass
