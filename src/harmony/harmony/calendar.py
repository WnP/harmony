'''
Functions for processing calendars.
'''


from pytz import timezone as pytz_timezone
from random import randint


class PersistableObject(object):
    def __init__(self, pk=None):
        self.pk = pk

    @classmethod
    def create(cls, **kwargs):
        '''
        Create a new instance of cls.

        @param kwargs: Keyword arguments to pass to the model (dict)
        @returns: The new object (cls)
        '''
        newobj = cls(**kwargs)
        newobj.save()
        return newobj

    def save(self):
        self.pk = randint(0, 65536)

    def __repr__(self):
        return "<{0.__class__.__name__} '{0}'>".format(self)

    def __str__(self):
        return str(unicode(self))


class Calendar(PersistableObject):
    '''A calendar.'''

    DEFAULT_NAME = u'Untitled Calendar'

    def __init__(self, name=DEFAULT_NAME, timezone=None, **kwargs):
        '''
        @param name: Name of this calendar (str)
        @param timezone: Timezone of this calendar (str)
        '''
        super(Calendar, self).__init__(**kwargs)
        self.name = name
        self.timezone = timezone
        self._events = []

    def __unicode__(self):
        return unicode(self.name)

    def add_event(self, event):
        self._events.append(event)


class Event(PersistableObject):
    '''An event. Events are individual entries in a calendar. An event can only
    exist as part of, or paired with, a Calendar object.'''

    DEFAULT_SUMMARY = u'Untitled event'

    def __init__(self, summary=DEFAULT_SUMMARY, start=None, end=None,
                 calendar=None, **kwargs):
        '''
        @param summary: The event's description, title, summary, whatever. (str)
        @param start: The start time of the event. (datetime)
        @param end: The end time of the event. (datetime)
        @param calendar: The calendar this event is associated with (Calendar)
        '''
        super(Event, self).__init__(**kwargs)
        self.summary = summary
        self.start = start
        self.end = end
        self.calendar = calendar

    def __unicode__(self):
        return unicode(self.summary)
