'''
Basic app data.
'''

from datetime import datetime, date
from os.path import expanduser as path_expanduser, join as path_join

from pytz import timezone as pytz_timezone, UnknownTimeZoneError

from .calendar import Calendar, Event
from .settings import Settings


# Harmony parameters
APP_AUTHOR = u'Eryn Wells'
APP_NAME = u'Harmony'
APP_VERSION = (0, 0, 1)
APP_VERSION_STRING = u'{0[0]:d}.{0[1]:d}{0[2]:d}'.format(APP_VERSION)

# iCalendar parameters
ICAL_PRODID = u'-//{author}//{name} {version}//EN'.format(
        author=APP_AUTHOR, name=APP_NAME, version=APP_VERSION_STRING)
ICAL_VERSION = (2, 0)
ICAL_VERSION_STRING = u'.'.join([str(vnum) for vnum in ICAL_VERSION])

# Configuration parameters
CONFIG_DIRECTORY = path_join(path_expanduser('~'), '.harmony')
CONFIG_HARMONY = path_join(CONFIG_DIRECTORY, 'harmony.conf')
CONFIG_CALENDARS_DB = path_join(CONFIG_DIRECTORY, 'calendars.db')


class Application(object):
    '''
    The heart of Harmony. The application logic. The (MVC) controller.
    '''

    def __init__(self):
        self.calendars = {}
        self.default_calendar = None

    def create_calendar(self, name, timezone=None, default=False):
        if timezone == None:
            # TODO: Get it from the configuration or the system.
            pass
        cal = Calendar.create(name=str(name), timezone=timezone,
                              default=default)
        self.calendars[cal.pk] = cal
        if default:
            self.default_calendar = cal

    def create_event(self, summary, calendar, start, end):
        cal = self.calendars.get(calendar_id)
        if cal is None:
            raise ValueError('Invalid calendar id: {0}'.format(calendar_id))
        ev = Event(summary=str(summary), calendar=cal, start=start, end=end)
        cal.add_event(ev)


# The application singleton instance. Any of the frontends should be pushing and
# pulling data, and performing actions on behalf of the user here.
app = Application()
# The settings singleton instance.
settings = Settings()
