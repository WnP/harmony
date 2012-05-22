'''
Basic app data.
'''

from os.path import expanduser as path_expanduser, join as path_join


# Harmony parameters
APP_AUTHOR = u'Eryn Wells'
APP_NAME = u'Harmony'
APP_VERSION = (0, 0, 1)
APP_VERSION_STRING = u'{}.{}{}'.format(VERSION)

# iCalendar parameters
ICAL_PRODID = u'-//{author}//{name} {version}//EN'.format(
        author=AUTHOR, name=NAME, version=VERSION_STRING)
ICAL_VERSION = (2, 0)
ICAL_VERSION_STRING = u'.'.join(ICAL_VERSION)

# Configuration parameters
CONFIG_DIRECTORY = path_join(path_expanduser('~'), '.harmony')
CONFIG_HARMONY = path_join(CONFIG_DIRECTORY, 'harmony.conf')
CONFIG_CALENDARS_DB = path_join(CONFIG_DIRECTORY, 'calendars.db')
