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


class Setting(object):
    '''A setting.'''

    def __init__(self, default=None, typ=None):
        self.default = default
        self.typ = typ

    def validate(self, new_value):
        if isinstance(new_value, self.typ):
            return True
        return False

    def transform(self, new_value):
        return new_value


class StringSetting(Setting):
    '''A setting field to hold a [unicode] string.'''

    def __init__(self, default=''):
        super(StringSetting, self).__init__(default, basestring)

    def transform(self, new_value):
        return unicode(new_value)


class TimezoneSetting(StringSetting):
    '''A setting field to hold a timezone.'''

    def transform(self, new_value):
        new_value = super(TimezoneSetting, self).transform(new_value)
        return pytz_timezone(new_value)


class HarmonySettings(object):
    '''
    A class to store all of the settings for the current run of Harmony.
    '''

    # The user's real name
    realname = StringSetting()
    # The user's timezone
    timezone = TimezoneSetting(default='UTC')

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
        desc = self._settings
        if value is None:
            value = desc.default
        if not desc.validate(value):
            raise ValueError("Invalid type ({}) for setting '{}'; "
                             "expected {}".format(type(value).__name__, name,
                                                  desc.typ))
        value = desc.transform(value)
        super(HarmonySettings, self).__setattr__(name, value)


# The application singleton instance. Any of the frontends should be pushing and
# pulling data, and performing actions on behalf of the user here.
app = HarmonyApp()
# The settings singleton instance.
settings = HarmonySettings()
