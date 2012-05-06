'''
Functions for processing calendars.
'''


import ConfigParser
from datetime import datetime
from os import listdir
from os.path import basename, join as path_join, splitext
from re import compile as re_compile
from uuid import uuid4

from icalendar import Calendar as vCalendar
from icalendar import Event as vEvent
from pytz import timezone as pytz_timezone
from pytz import utc

from .. import app
from .config import CALENDAR_DIRECTORY, CALENDAR_CONFIG


REGEX_WS = re_compile(r'\s')

# Calendar cache
CALENDARS = {}


class Calendar(object):
    '''A calendar.'''

    DEFAULT_NAME = u'Untitle Calendar'

    def __init__(self, uuid=None, name=None, timezone=None):
        self.uuid = uuid
        self.name = name
        self.timezone = pytz_timezone(timezone)
        self.events = {}

    @property
    def directory(self):
        '''Directory containing this calendar. Auto-generated.'''
        if self.uuid is None:
            raise AttributeError(
                    "'{0.__name__}' object has no attribute 'uuid';"
                    'cannot generate directory name'.format(type(self)))
        return path_join(CALENDAR_DIRECTORY, '{}.calendar'.format(self.uuid))

    def load_events(self):
        '''Read all the events in the calendar's directory and add them to the
        calendar.'''
        for vevent_file in listdir(self.directory):
            event = Event.create_from_ical_file(vevent_file)
            self.add_event(event)

    def add_event(self, event):
        '''Add an event to this calendar.'''
        self.events[event.uuid] = event


class Event(object):
    '''An event.'''

    PRODID = u'-//{author}//{name} {version}//EN'.format(
            author=app.AUTHOR,
            name=app.NAME,
            version=app.VERSION_STRING)

    DEFAULT_SUMMARY = u'Untitled event'

    # Commonly used, but not part of the standard, iCalendar attributes
    CALNAME = 'X-WR-CALNAME'
    TIMEZONE = 'X-WR-TIMEZONE'

    def __init__(self, uuid=None, summary=None, begin=None, end=None):
        self.uuid = uuid

        self.vcal = vCalendar()
        self.vcal.add('VERSION', u'2.0')
        self.vcal.add('PRODID', Event.PRODID)
        self.vcal.add('CALSCALE', u'GREGORIAN')

        self.vevent = vEvent()
        self.vevent.add('SUMMARY', unicode(summary)
                if summary is not None else Event.DEFAULT_SUMMARY)

        self.vevent.add('CREATED', datetime.now(tz=utc))
        self.vevent.add('DTSTART', begin if begin is not None else
                        datetime.now(tz=utc))
        self.vevent.add('DTEND', end if end is not None else
                        datetime.now(tz=utc))

        self.vcal.add_component(self.vevent)

    @classmethod
    def create_from_ical_file(cls, ical_filename):
        '''Given a filename, create an Event and return it.'''
        uuid = splitext(basename(ical_filename))[1]
        event = Event(uuid=uuid)
        event.from_ical(open(ical_filename, 'r').read())
        return event

    @property
    def filename(self):
        '''iCalendar event object filename.'''
        return '{}.ics'.format(self.uuid)

    def to_ical(self):
        '''Render this event as an iCalendar object.'''
        return self.vcal.to_ical()

    def from_ical(self, ical):
        '''Read an iCalendar object from the passed-in string.'''
        self.vcal.from_ical(ical)


def create_calendar(name, timezone=None):
    '''Create a new calendar.'''
    uuid = uuid4()
    cal = Calendar(uuid=uuid, name=name, timezone=timezone)
    CALENDARS[uuid] = cal
    return cal


def read_calendar(uuid, name, timezone):
    '''Read an iCalendar from a file and return its Python representation.'''
    cal = Calendar(uuid=uuid, name=name, timezone=timezone)
    cal.load_events()
    return cal


def load_calendars():
    '''Read the calendar config file and load all calendars into the cache.'''
    config = ConfigParser.SafeConfigParser()
    config.readfp(open(CALENDAR_CONFIG))
    for uuid in config.sections():
        CALENDARS[uuid] = read_calendar(uuid=uuid,
                                        name=config.get(uuid, 'name'),
                                        timezone=config.get(uuid, 'timezone'))
