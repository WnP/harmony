'''
Functions for processing calendars.
'''


import ConfigParser
from datetime import datetime
from os import listdir, mkdir
from os.path import basename, join as path_join, splitext
from re import compile as re_compile
from uuid import UUID, uuid4

from icalendar import Calendar as vCalendar, Event as vEvent
from pytz import timezone as pytz_timezone, utc

from .. import app
from .config import CALENDAR_DIRECTORY, CALENDAR_CONFIG


REGEX_WS = re_compile(r'\s')
NOW = lambda: datetime.now(tz=utc)


class Calendar(object):
    '''A calendar. Calendars are actually made of two components: an entry in
    the calendars configuration file and a <uuid>.calendar directory in the
    calendars directory. Thus, a Calender is really just a container for Events,
    where each event is a file in the Calendar's directory.'''

    DEFAULT_NAME = u'Untitled Calendar'

    def __init__(self, uuid=None, name=None, timezone=None):
        self.uuid = uuid
        self.name = unicode(name)
        self.timezone = pytz_timezone(timezone)
        self.events = {}
        self._dirty = True

    @property
    def directory(self):
        '''Directory containing this calendar. Auto-generated.'''
        if self.uuid is None:
            raise AttributeError(
                    "'{0.__name__}' object has no attribute 'uuid';"
                    'cannot generate directory name'.format(type(self)))
        return path_join(CALENDAR_DIRECTORY, '{}.calendar'.format(self.uuid))

    def __str__(self):
        return self.name

    def __unicode__(self):
        return unicode(str(self))

    def __repr__(self):
        return u"<Calendar '{}'>".format(unicode(self))

    def save(self, force=False):
        if not self._dirty and not force:
            return
        try:
            mkdir(self.directory)
        except OSError:
            pass
        with open(CALENDAR_CONFIG, 'w') as calendar_config:
            CONFIG.write(calendar_config)
        self._dirty = False

    def load_events(self):
        '''Read all the events in the calendar's directory and add them to the
        calendar.'''
        for vevent_file in listdir(self.directory):
            full_path = path_join(self.directory, vevent_file)
            event = Event.create_from_ical_file(self, full_path)
            self.add_event(event)
        self._dirty = False

    def add_event(self, event):
        '''Add an event to this calendar.'''
        self.events[str(event.uuid)] = event
        event._calendar = self


class Event(object):
    '''An event.'''

    PRODID = u'-//{author}//{name} {version}//EN'.format(
            author=app.AUTHOR,
            name=app.NAME,
            version=app.VERSION_STRING)

    DEFAULT_SUMMARY = u'Untitled event'

    class EventError(RuntimeError):
        pass

    def __init__(self, uuid=None, summary=None, start=None, end=None):
        self._calendar = None
        self._dirty = True

        self.uuid = uuid
        self.summary = summary
        self.start = start
        self.end = end

    @classmethod
    def create_from_ical_file(cls, calendar, ical_filename):
        '''Given a filename, create an Event and return it.'''
        uuid = splitext(basename(ical_filename))[0]
        event = Event(uuid=uuid)
        with open(ical_filename, 'r') as ical_file:
            event.from_ical(ical_file.read())
        return event

    def __str__(self):
        return self.summary

    def __unicode__(self):
        return unicode(str(self))

    def __repr__(self):
        return u"<Event '{}'>".format(unicode(self))

    @property
    def filename(self):
        '''iCalendar event object filename.'''
        return path_join(self.calendar.directory, '{}.ics'.format(self.uuid))

    @property
    def summary(self):
        return str(self.vevent.get('SUMMARY'))

    @summary.setter
    def summary(self, value):
        self.vevent.set('SUMMARY', value)

    @property
    def start(self):
        return self.vevent.get('DTSTART').dt

    @start.setter
    def start(self, value):
        self.vevent.set('DTSTART', value.astimezone(utc))

    @property
    def end(self):
        return self.vevent.get('DTEND').dt

    @end.setter
    def end(self, value):
        return self.vevent.set('DTEND', value.astimezone(utc))

    def _validate(self):
        if not isinstance(self.uuid, UUID):
            raise TypeError('uuid must be a UUID instance')
        if not isinstance(self.summary, basestring):
            raise TypeError('summary must be a str or unicode instance')
        if not isinstance(self.start, datetime):
            raise TypeError('start must be a datetime instance')
        if not isinstance(self.end, datetime):
            raise TypeError('end must be a datetime instance')

    def _clean(self):
        self.summary = unicode(self.summary)
        self.start = self.start.astimezone(utc)
        self.end = self.end.astimezone(utc)

    def save(self, force=False):
        if not self._dirty and not force:
            return

        self._validate()
        self._clean()

        with open(self.filename, 'w') as ical_file:
            ical_file.write(self.to_ical())

        self._dirty = False

    def to_ical(self):
        '''Render this event as an iCalendar object.'''
        vcal = vCalendar()
        vcal.add('VERSION', app.ICALENDAR_VERSION)
        vcal.add('PRODID', Event.PRODID)
        vcal.add('CALSCALE', 'GREGORIAN')

        vevent = vEvent()
        vevent.add('CREATED', NOW())
        vevent.add('SUMMARY', self.summary)
        vevent.add('DTSTART', self.start)
        vevent.add('DTEND', self.end)
        vcal.add_component(self.vevent)

        return vcal.to_ical()

    def from_ical(self, ical):
        '''Read an iCalendar object from the passed-in string.'''
        self.vcal.from_ical(ical)


def create_calendar(name, timezone=None):
    '''Create a new calendar.'''
    uuid = str(uuid4())
    cal = Calendar(uuid=uuid, name=name, timezone=timezone)
    return cal


def read_calendar(uuid, name, timezone):
    '''Read an iCalendar from a file and return its Python representation.'''
    cal = Calendar(uuid=uuid, name=name, timezone=timezone)
    cal.load_events()
    return cal


def read_calendars():
    '''Read the calendar config file and load all calendars found therein. A
    dictionary mapping UUIDs to Calendar objects is returned.'''
    config = ConfigParser.SafeConfigParser()
    with open(CALENDARS_CONF) as cals_file:
        config.readfp(cals_file)
    calendars = {}
    for uuid in config.sections():
        calendars[uuid] = read_calendar(uuid=uuid,
                                        name=CONFIG.get(uuid, 'name'),
                                        timezone=CONFIG.get(uuid, 'timezone'))
    return calendars


def create_event(calendar, summary, start, end):
    '''Create a new event in the specified calendar.'''
    ev = Event(uuid=str(uuid4()), start=start, end=end)
    calendar.add_event(ev)
    return ev
