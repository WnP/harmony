'''
Basic app data.
'''


# Harmony parameters
AUTHOR = u'Eryn Wells'
NAME = u'Harmony'
VERSION = (0, 0, 1)
VERSION_STRING = u'{}.{}{}'.format(VERSION)

# iCalendar parameters
ICAL_PRODID = u'-//{author}//{name} {version}//EN'.format(
        author=AUTHOR, name=NAME, version=VERSION_STRING)
ICAL_VERSION = (2, 0)
ICAL_VERSION_STRING = u'.'.join(ICAL_VERSION)
