import logging
from datetime import datetime

from pymoodle_jku.Client.client import MoodleClient
from pymoodle_jku.Utils.printing import print_array_results_table

logger = logging.getLogger(__name__)


def main(client: MoodleClient, args):
    timetable = client.calendar()

    objects = {}
    for t in timetable:
        if t.course_id not in objects:
            objects[t.course_id] = [t]
        else:
            objects[t.course_id].append(t)

    for id, t_list in objects.items():
        output = []
        print(t_list[0].course_fullname)
        for t in t_list:
            date = datetime.fromtimestamp(t.timestart).strftime("%Y-%m-%d %H:%M:%S")
            output.append([t.name, t.eventtype, date, t.url])
            print_array_results_table(output, ['Name', 'Type', 'Date', 'Link'])

    if __name__ == "__main__":
        pass
