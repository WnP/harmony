'''
Functions for handling config directories and files.

The harmony and calendars config files are ini files, parsed by ConfigParser.
'''

from os.path import join as path_join
from os.path import expanduser as path_expanduser


CONFIG_DIRECTORY = path_join(path_expanduser('~'), '.harmony')
CALENDAR_DIRECTORY = path_join(CONFIG_DIRECTORY, 'calendars')

CALENDAR_CONFIG = path_join(CALENDAR_DIRECTORY, 'calendars.conf')
HARMONY_CONFIG = path_join(CONFIG_DIRECTORY, 'harmony.conf')
