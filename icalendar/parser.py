'''An iCalendar object parser. {{{

From RFC 2445:

    contentline = name *(";" param ) ":" value CRLF
    name = x-name / iana-token
    iana-token = 1*(ALPHA / DIGIT / "-")
        ; iCalendar identifier registered with IANA
    x-name = "X-" [vendorid "-"] 1*(ALPHA / DIGIT / "-")
        ; Reservered for experimental use. Not intended for use in
        ; released products.
    vendorid = 3*(ALPHA / DIGIT)
        ;Vendor identification
    param = param-name "=" param-value *("," param-value)
        ; Each property defines the specific ABNF for the parameters
        ; allowed on the property. Refer to specific properties for
        ; precise parameter ABNF.
    param-name = iana-token / x-token
    param-value = paramtext / quoted-string
    paramtext = *SAFE-CHAR
    value = *VALUE-CHAR
    quoted-string = DQUOTE *QSAFE-CHAR DQUOTE
    NON-US-ASCII = %x80-F8
        ; Use restricted by charset parameter on outer MIME object
        ; (UTF-8 preferred)
    QSAFE-CHAR = WSP / %x21 / %x23-7E / NON-US-ASCII
        ; Any character except CTLs and DQUOTE
    SAFE-CHAR  = WSP / %x21 / %x23-2B / %x2D-39 / %x3C-7E / NON-US-ASCII
        ; Any character except CTLs, DQUOTE, ";", ":", ","
    VALUE-CHAR = WSP / %x21-7E / NON-US-ASCII
        ; Any textual character
    CR = %x0D ; carriage return
    LF = %x0A ; line feed
    CRLF = CR LF ; Internet standard newline
    CTL = %x00-08 / %x0A-1F / %x7F ; Controls
    ALPHA = %x41-5A / %x61-7A   ; A-Z / a-z
    DIGIT = %x30-39 ; 0-9
    DQUOTE = %x22 ; Quotation Mark
    WSP = SPACE / HTAB
    SPACE = %x20
    HTAB = %x09

Parsing proceeds in the following manner:

    1. Read a line (until a CRLF *not* followed by a WSP character)
    2. Unfold if necessary (remove CRLF WSP sequences)
    3. Parse content line
}}}'''


from __future__ import print_function
import langspec


class ICalendarObject(list):
    'An iCalendar object.'


class ICalendarContentLine:
    'An iCalenadr content line.'

    def __init__(self, name, value, params=None):
        self.name = name
        self.value = value
        self.params = params if params is not None else []

    def __str__(self):
        param_string = ';'.join(self.params)
        return '{0.name}{1}{2}:{0.value}{3}'.format(self,
                ';' if param_string != '' else '', param_string,
                langspec.CRLF.pattern)


def parse(data):
    '''
    Parse raw_data into an ICalendarObject and return it.

    @param data: The data to parse (subclass of basestring)
    @returns: The parsed data (object)
    @raises: TypeError on invalid input
    '''
    if not issubclass(data, basestring):
        raise TypeError('Invalid type {} for incoming data'.format(
                        type(data).__name__))
    return _lex_ical_object(data)


def _lex_ical_object(data):
    '''
    Lex the iCalendar object into a top-level ICalendarObject and a list of
    ICalendarContentLine objects. The result has no semantic meaning, it's just
    tokenized.

    @param data: The data to lex (str)
    @returns: The lexed data (ICalendarObject)
    '''
    obj = ICalendarObject()
    lines = langspec.CRLF.split(_unfold(data))
    for line in lines:
        print(line)
        m = langspec.CONTENT_LINE.search(line)
        if m is None:
            raise RuntimeError('Invalid iCalendar line: {}'.format(line))
        line_components = dict(m.groupdict())
        params = line_components['params']
        if params == '':
            line_components['params'] = []
        else:
            # First element of the list will always be '' because of how the
            # regex extracts the param list
            params = params.split(';')[1:]
            line_components['params'] = params
        obj.append(ICalendarContentLine(**line_components))
    return obj


def _unfold(data):
    '''Perform any necessary unfolding on the incoming data. Return the unfolded
    data.'''
    return langspec.FOLD_MARKER.sub('', data)
