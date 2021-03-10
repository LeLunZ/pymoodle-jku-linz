import time
from argparse import Namespace

from pymoodle_jku.classes.course import Course, parse_course_name
from pymoodle_jku.client.client import MoodleClient
from pymoodle_jku.utils.login import relogin
from pymoodle_jku.utils.printing import print_pick_results_table, clean_screen, print_array_results_table


@relogin
def main(client: MoodleClient, args: Namespace):
    now = int(time.time())
    old_filter = lambda c, t=now: c.enddate >= t or c.enddate is None or c.enddate == 0
    if args.search:
        filter_exp = lambda c, search=args.search: any(s.lower() in c.fullname.lower() for s in search)
        if not args.old:
            old_filter_exp = filter_exp
            filter_exp = lambda c, t=now: old_filter_exp(c) and old_filter(c)
        courses = client.courses(load_pages=False, filter_exp=filter_exp)
        evals = client.multi_valuation(courses)
        for c, eval in evals:
            print(f' {c.fullname}')
            if len(eval) == 0:
                print('No Evaluations\n')
            else:
                print_array_results_table([(f'{e.name}', f'{e.grade}', f'{e.grade_range}') for e in eval],
                                          ['Name', 'Points', 'Range'])

            if not args.quiet:
                input('Press [Enter] to continue')
            print()
            print()
        print('Nothing else found')
        return 0

    valuations = client.valuation_overview()
    original_valuations = valuations
    if not args.old:
        courses = client.courses(load_pages=False, filter_exp=old_filter)
        courses = sorted(courses, reverse=True)
        course_ids = [c.id for c in courses]
        valuations = dict([(key, val) for key, val in valuations.items() if key in course_ids])
    else:
        courses = client.courses(load_pages=False)
        courses = sorted(courses, reverse=True)
        valuations = dict([(key, val) for key, val in valuations.items()])
    if len(courses) == 0:
        print('No Courses to display. Try [-o] for older courses.')
        return 0
    if args.quiet:
        print_array_results_table([(f'{parse_course_name(val[0])}', f'{val[1]}') for key, val in valuations.items()],
                                  ['Course', 'Points'])
    else:
        vals = []
        loaded_more = False
        for c in courses:
            if c.id in valuations.keys():
                vals.append([c.parse_name(), valuations[c.id][1]])
            else:
                vals.append([c.parse_name(), '-'])
        while True:
            clean_screen()
            element, index = print_pick_results_table(vals)
            if index == -1:
                return 0
            if index == -2:
                # load more data if possible
                if not args.old and not loaded_more:
                    loaded_more = True
                    courses = client.courses(load_pages=False)
                    courses = sorted(courses, reverse=True)
                    vals = []
                    for c in courses:
                        if c.id in original_valuations.keys():
                            vals.append([c.parse_name(), original_valuations[c.id][1]])
                        else:
                            vals.append([c.parse_name(), '-'])
                continue
            course = courses[index]
            evaluations = client.single_valuation(course)
            clean_screen()
            if len(evaluations) == 0:
                continue
            print(course.fullname)
            print_array_results_table([(f'{e.name}', f'{e.grade}', f'{e.grade_range}') for e in evaluations],
                                      ['Name', 'Points', 'Range'])
            enter_press = input('\nPress Enter to continue')
