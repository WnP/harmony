'''
Basic app data.
'''

from datetime import datetime, date
from os.path import expanduser as path_expanduser, join as path_join

from pytz import timezone as pytz_timezone, UnknownTimeZoneError

from harmony.calendar import Calendar, Event


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


class HarmonyApp(object):
    '''
    The heart of Harmony. The application logic. The (MVC) controller.
    '''

    def __init__(self):
        self.calendars = {}

    def create_calendar(self, name, timezone=None):
        if timezone == None:
            # TODO: Get it from the configuration or the system.
            pass
        cal = Calendar.create(name=str(name), timezone=timezone)
        self.calendars[cal.pk] = cal

    def create_event(self, summary, calendar, start, end):
        cal = self.calendars.get(calendar_id)
        if cal is None:
            raise ValueError('Invalid calendar id: {0}'.format(calendar_id))
        ev = Event(summary=str(summary), calendar=cal, start=start, end=end)
        cal.add_event(ev)


class HarmonySettings(object):
    '''
    A class to store all of the settings for the current run of Harmony.
    '''

    realname = {'type': str}
    timezone = {'type': str,
                'transform': pytz_timezone,
                'default': 'US/Pacific'}

    def __new__(cls, *args, **kwargs):
        new_settings = super(HarmonySettings, cls).__new__(cls, *args, **kwargs)
        super(HarmonySettings, new_settings).__setattr__('_settings', {})
        for stg, desc in vars(cls).iteritems():
            if stg.startswith('__') and stg.endswith('__'):
                continue
            if not isinstance(desc, dict):
                continue
            new_settings._settings[stg] = desc
            setattr(new_settings, stg, desc.get('default'))
        return new_settings

    def __setattr__(self, name, value):
        desc = self._settings[name]
        if not isinstance(value, desc['type']):
            raise ValueError("Invalid type ({}) for setting '{}'; "
                             "expected {}".format(type(value).__name__, name,
                                                  desc['type'].__name__))
        tr = desc.get('transform')
        if tr is not None:
            value = tr(value)
        super(HarmonySettings, self).__setattr__(name, value)


# The application singleton instance. Any of the frontends should be pushing and
# pulling data, and performing actions on behalf of the user here.
app = HarmonyApp()
# The settings singleton instance.
settings = HarmonySettings()
