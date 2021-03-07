from examples.moodle_client import simple_client


def calendar():
    # get a moodle calendar
    # Returns a List of Events
    calendar_events = client.calendar()

    for event in calendar_events:
        print(event.name, end=' ')
        print(event.eventtype, end=' ')
        print(event.timesort)

    # its also possible to limit the events
    calendar_events = client.calendar(limit=10)
    print(calendar_events)


if __name__ == '__main__':
    client = simple_client()
    calendar()
