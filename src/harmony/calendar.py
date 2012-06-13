'''
Functions for processing calendars.
'''


from pytz import timezone as pytz_timezone
from random import randint

from .persistence import model


class Calendar(model.Model):
    '''A calendar.'''

    name = model.TextField(unique=True, default='Untitled Calendar')
    timezone = model.TimezoneField()
    is_default = model.BooleanField(default=False)

    def __unicode__(self):
        return unicode(self.name)


class Event(model.Model):
    '''An event.'''

    summary = model.TextField(default='Untitled event')
    all_day = model.BooleanField(default=False)
    start = model.DateTimeField()
    end = model.DateTimeField()
    calendar = model.ForeignKeyField(Calendar)

    def __unicode__(self):
        return unicode(self.summary)
