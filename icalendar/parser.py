#
#
#

'''
An iCalendar object parser.

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
'''


from StringIO import StringIO


class ICalendarObject:
    'An iCalendar object.'

    def __init__(self):
        self.content_lines = []


class ICalendarContentLine:
    'An iCalenadr content line.'

    def __init__(self, name, value, params=None):
        self.name = name
        self.value = value
        self.params = params if params is not None else []


def parse(data):
    'Parse raw_data into an ICalendarObject and return it.'
    if hasattr(data, 'read'):
        # Stream
        pass
    elif issubclass(data, basestring):
        data = StringIO(data)
    else:
        raise TypeError('Invalid type {} for incoming data'.format(
                        type(data).__name__))
    return _parse_stream(data)

def _parse_stream(stream):
    pass
