from argparse import Namespace

from pymoodle_jku.Classes.course import Course
from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Utils.printing import print_results_table, clean_screen, print_array_results_table


def main(client: MoodleClient, args: Namespace):
    if args.search:
        courses = filter(lambda c: any(s.lower() in c.fullname.lower() for s in args.search),
                         client.courses(load_pages=False))
        evals = client.multi_valuation_overview(courses)
        for c, eval in evals:
            print(f' {c.fullname}')
            if len(eval) == 0:
                print('\nNo Evaluations')
            else:
                print_array_results_table([(f'{e.name}', f'{e.grade}', f'{e.grade_range}') for e in eval],
                                          ['Name', 'Points', 'Range'])

            if not args.quiet:
                input('Press [Enter] to continue')
            print()
            print()
        print('Nothing else found')
        exit(0)
    valuations = client.valuation_overview()
    if args.quiet:
        print_results_table(valuations, ['Course', 'Points'])
    else:
        courses = client.courses(load_pages=False)
        vals = {}
        for c in courses:
            if c.fullname in valuations.keys():
                vals[c] = valuations[c.fullname]
        while True:
            course: Course = print_results_table(vals, ['Course', 'Points'], quiet=False)
            clean_screen()
            if course is None:
                exit(0)
            else:
                evaluations = client.single_valuation_overview(course)
                clean_screen()
                if len(evaluations) == 0:
                    continue
                print(course.fullname)
                print_array_results_table([(f'{e.name}', f'{e.grade}', f'{e.grade_range}') for e in evaluations],
                                          ['Name', 'Points', 'Range'])
                enter_press = input('\nPress Enter to continue')
                clean_screen()
            pass
