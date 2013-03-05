'''
CalDAV client implementation.
'''

import datetime
import requests
import urlobject
import xml.parsers.expat


class CalDAVClient(object):
    '''
    CalDAV Client.
    '''

    def __init__(self, url=None, auth=None):
        self.url = urlobject.URLObject(url)
        self.auth = auth

    def _requests_kwargs(self):
        kwargs = {}
        if self.auth is not None:
            kwargs['auth'] = self.auth
        return kwargs

    def fetch_options(self):
        kwargs = {}
        if self.auth is not None:
            kwargs['auth'] = self.auth
        r = requests.options(str(self.url), **kwargs)
        r.raise_for_status()

        options = dict(r.headers)
        options['allow'] = [field.strip().upper() for field in r.headers['allow'].split(',')]
        options['dav'] = [field.strip().lower() for field in r.headers['dav'].split(',')]
        if 'PROPFIND' not in allow_header:
            return None
        if 'calendar-access' not in dav_header:
            return None
        try:
            options['date'] = datetime.datetime.fromtimestamp(options['date'])
        except KeyError:
            pass
        try:
            options['expires'] = datetime.datetime.fromtimestamp(options['expires'])
        except KeyError:
            pass
        return options

    def fetch_calendar_descriptors(self):
        '''
        Fetch and return a list of CalendarDescriptor objects from the CalDAV server.
        '''
        r = requests.request('PROPFIND', str(self.url), **self._requests_kwargs())
        r.raise_for_status()
        return CalDAVRootParser.parse(r.content)



class CalendarDescriptor(object):
    '''
    Description of a calendar object from CalDAV.
    '''

    def __init__(self, **kwargs):
        # WebDAV properties
        self.href = kwargs.get('href')
        self.content_type = kwargs.get('content_type')
        self.name = kwargs.get('name')
        # CalDAV properties
        self.color = kwargs.get('color')
        self.order = kwargs.get('order')
        self.description = kwargs.get('description')


class CalDAVRootParser(object):
    '''
    Parser for the root of the CalDAV collection.
    '''

    def __init__(self):
        self._calendars = None
        self._parser = xml.parsers.expat.ParserCreate()
        self._tags = None
        self._bucket = None

    @classmethod
    def parse(cls, data):
        parser = cls()

        # Initialize global parser state
        parser._tags = []

        # Set up the parser
        parser._parser.StartElementHandler = parser._start_element
        parser._parser.EndElementHandler = parser._end_element
        parser._parser.CharacterDataHandler = parser._character_data

        # Off we go...
        if isinstance(data, basestring):
            parser._parser.Parse(data)
        else:
            parser._parser.ParseFile(data)
        return parser._calendars

    def _split_namespace(self, name):
        try:
            ns, tag = name.split(':')
        except ValueError:
            ns = ''
            tag = name
        return ns, tag

    def _start_element(self, name, attribs):
        ns, tag = self._split_namespace(name)
        self._tags.append(tag)
        if tag == 'response':
            # Potential calendar entry
            self._bucket = {}
        elif len(self._tags) >= 2 and self._tags[-2] == 'resourcetype':
            if 'types' not in self._bucket:
                self._bucket['types'] = []
            self._bucket['types'].append(tag)

    def _end_element(self, name):
        ns, tag = self._split_namespace(name)
        if self._tags[-1] != tag:
            raise ValueError('Wat.')
        self._tags.pop()
        if tag == 'response':
            # End of potential calendar entry. Check types and dump the bucket
            # if its not a calendar.
            if self._bucket and 'types' in self._bucket:
                if 'calendar' in self._bucket['types']:
                    if self._calendars is None:
                        self._calendars = []
                    self._calendars.append(CalendarDescriptor(**self._bucket))
                else:
                    # Dump the bucket! (This is not a Calendar element.)
                    self._bucket = None

    def _character_data(self, data):
        try:
            currtag = self._tags[-1]
        except IndexError:
            # Ignore data if there are no tags on the stack.
            return
        if currtag == 'href':
            self._bucket['href'] = data
        elif currtag == 'displayname':
            self._bucket['name'] = data
        elif currtag == 'contenttype':
            self._bucket['content_type'] = data
        elif currtag == 'calendar-color':
            self._bucket['color'] = data
        elif currtag == 'calendar-order':
            self._bucket['order'] = data
        elif currtag == 'calendar-description':
            self._bucket['description'] = data
