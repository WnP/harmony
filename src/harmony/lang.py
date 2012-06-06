'''
Cute little pidgin SQL for doing things with Harmony.
'''


import datetime
import re
import shlex

from pytz import timezone


################################################################################
## KEYWORDS


_keyword = lambda regex: re.compile(regex, flags=re.IGNORECASE)

AT = _keyword('AT')
CREATE = _keyword('CREATE')
CALENDAR = _keyword('CALENDAR')
CALENDARS = _keyword('CALENDARS')
DEFAULT = _keyword('DEFAULT')
EQUAL = _keyword('=')
EVENT = _keyword('EVENT')
EVENTS = _keyword('EVENTS')
FOR = _keyword('FOR')
FROM = _keyword('FROM')
IN = _keyword('IN')
LIST = _keyword('LIST')
ON = _keyword('ON')
QUIT = _keyword('QUIT')
SET = _keyword('SET')
TIMEZONE = _keyword('TIMEZONE')
UNTIL = _keyword('UNTIL')

DAYS = _keyword('DAYS?')
HOURS = _keyword('HOURS?')
MINUTES = _keyword('MINUTES?')
WEEKS = _keyword('WEEKS?')
TIME_TOKENS = (DAYS, HOURS, MINUTES, WEEKS)

LITERAL = _keyword('\w+')
NUMBER = _keyword('\d+(\.\d*)?')

# Acceptable date and time formats
DATE_FMTS = ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y')
TIME_FMTS = ('%H:%M',)


################################################################################
## TOP LEVEL


def process_line(line):
    return analyze(parse(shlex.split(line)))


################################################################################
## PARSER


def parse(tokens):
    '''Parse a list of tokens into a dictionary of its components.'''
    if accept(CREATE, tokens):
        stmt = parse_create_stmt(tokens)
    elif accept(LIST, tokens):
        stmt = parse_list_stmt(tokens)
    elif accept (SET, tokens):
        stmt = parse_set_stmt(tokens)
    elif accept(QUIT, tokens):
        stmt = {'action': 'quit'}
    expect_eol(tokens)
    return stmt


def parse_create_stmt(tokens):
    stmt = {'action': 'create'}
    default = False
    if accept(DEFAULT, tokens):
        default = True
        expect_peek(CALENDAR, tokens)
    if accept(CALENDAR, tokens):
        stmt['type'] = 'calendar'
        stmt['default'] = default
        if expect_peek(LITERAL, tokens):
            stmt['name'] = tokens.pop(0)
        try:
            stmt.update(parse_in_timezone_clause(tokens))
        except HarmonyInitialTokenMissingError:
            pass
    elif accept(EVENT, tokens):
        stmt['type'] = 'event'
        if expect_peek(LITERAL, tokens):
            stmt['name'] = tokens.pop(0)
        if accept(IN, tokens):
            expect(CALENDAR, tokens)
            if expect_peek(LITERAL, tokens):
                stmt['calendar'] = tokens.pop(0)
        if expect(FROM, tokens):
            stmt['from'] = parse_time_clause(tokens)
        if accept(UNTIL, tokens):
            stmt['until'] = parse_time_clause(tokens)
        elif accept(FOR, tokens):
            stmt['for'] = parse_duration_clause(tokens)
        else:
            error(tokens, '{0.pattern} or {1.pattern}'.format(UNTIL, FOR))
    return stmt


def parse_list_stmt(tokens):
    stmt = {'action': 'list'}
    if accept(CALENDARS, tokens):
        stmt['type'] = 'calendar'
    elif accept(EVENTS, tokens):
        stmt['type'] = 'event'
    return stmt


def parse_set_stmt(tokens):
    stmt = {'action': 'set'}
    if expect_peek(LITERAL, tokens):
        stmt['setting'] = tokens.pop(0)
    expect(EQUAL, tokens)
    # TODO: Not all settings will be literals; some will probably be numbers and
    # other things. So, this regex needs to be expanded.
    if expect_peek(LITERAL, tokens):
        stmt['value'] = tokens.pop(0)
    return stmt


def parse_time_clause(tokens):
    stmt = {}
    initial_literal = None
    if expect_peek(LITERAL, tokens):
        initial_literal = tokens.pop(0)
    if accept(AT, tokens):
        stmt['date'] = initial_literal
        if expect_peek(LITERAL, tokens):
            stmt['time'] = tokens.pop(0)
            try:
                stmt.update(parse_in_timezone_clause(tokens))
            except HarmonyInitialTokenMissingError:
                pass
    else:
        stmt['time'] = initial_literal
        try:
            stmt.update(parse_in_timezone_clause(tokens))
        except HarmonyInitialTokenMissingError:
            pass
        if accept(ON, tokens):
            if expect_peek(LITERAL, tokens):
                stmt['date'] = tokens.pop(0)
    return stmt


def parse_in_timezone_clause(tokens):
    try:
        expect(IN, tokens)
    except HarmonySyntaxError as e:
        raise HarmonyInitialTokenMissingError(e.found, e.expected)
    expect(TIMEZONE, tokens)
    if expect_peek(LITERAL, tokens):
        return {'timezone': tokens.pop(0)}


def parse_duration_clause(tokens):
    stmt = {}
    while peek(NUMBER, tokens):
        num = float(tokens.pop(0))
        for tok in TIME_TOKENS:
            if peek(tok, tokens):
                stmt[tokens.pop(0).lower()] = num
                break
        else:
            error(tokens, ' or '.join([tok.pattern for tok in TIME_TOKENS]))
    return stmt


#
# Parser helpers
#

def accept(target, tokens, pop=True):
    '''By calling this function, the caller is declaring that it is acceptable
    for {tokens[0]} to match {target}. If {pop} is True, consume it; otherwise,
    leave the token in the list for the caller to deal with. If {tokens[0]}
    doesn't match {target} or there aren't any more tokens in the stream, return
    False.'''
    try:
        does_match = target.match(tokens[0]) is not None
    except IndexError:
        return False
    if does_match:
        if pop:
            tokens.pop(0)
        return True
    else:
        return False


def peek(target, tokens):
    '''Look at the top of the token stream. Return True if the top token matches
    {target}. Do not remove the top token from the list.'''
    return accept(target, tokens, pop=False)


def expect(target, tokens):
    '''By calling this function, the caller is declaring that the top token
    *must* be {target}. If the top token matches, consume it. If {target} does
    not match {tokens[0]}, raise an exception.'''
    if accept(target, tokens):
        return True
    error(tokens, target.pattern)


def expect_peek(target, tokens):
    '''Look at the top of the token stream. Return True if the top token matches
    {token}; raise an exception if it doesn't.'''
    if peek(target, tokens):
        return True
    error(tokens, target.pattern)


def expect_eol(tokens):
    '''Check if there are any tokens left in the token stream; raise an
    exception if {tokens} is not empty.'''
    if len(tokens) > 0:
        raise HarmonySyntaxError(tokens[0], 'end of line')


def error(tokens, expected):
    '''Raise a syntax or EOL error.'''
    try:
        raise HarmonySyntaxError(tokens[0], expected)
    except IndexError:
        raise HarmonyEOLError()


################################################################################
## SEMANTIC ANALYZER


def analyze(stmt):
    fmt = 'analyze_{0[action]}'
    if 'type' in stmt:
        fmt += '_{0[type]}'
    analyze_func = globals().get(fmt.format(stmt))
    if analyze_func:
        return analyze_func(stmt)
    else:
        return stmt


def analyze_create_calendar(calendar):
    if 'timezone' in calendar:
        calendar['timezone'] = timezone(calendar['timezone'])
    return calendar


def analyze_create_event(event):
    if 'from' in event:
        event['from'] = get_datetime(event['from'])
    if 'until' in event:
        event['until'] = get_datetime(event['until'])
    if 'for' in event:
        event['for'] = get_duration(event['for'])
    return event


#
# Semantic analyzer helpers
#


def transform_datetime(datetime_string, fmts):
    for fmt in fmts:
        try:
            return datetime.datetime.strptime(datetime_string, fmt)
        except ValueError:
            pass
    raise ValueError('Invalid datetime string: {}'.format(datetime_string))


def get_datetime(dt_dict):
    time = None
    date = None
    if 'time' in dt_dict:
        time = get_time(dt_dict['time'], dt_dict.get('timezone'))
    if 'date' in dt_dict:
        date = get_date(dt_dict['date'])
    if time is not None and date is not None:
        return datetime.datetime.combine(date, time)
    elif time is not None:
        return time
    elif date is not None:
        return date


def get_time(time_string, tz=None):
    dt = transform_datetime(time_string, TIME_FMTS)
    if tz is None:
        return datetime.time(hour=dt.hour, minute=dt.minute)
    else:
        return datetime.time(hour=dt.hour, minute=dt.minute,
                             tzinfo=timezone(tz))


def get_date(date_string):
    dt = transform_datetime(date_string, DATE_FMTS)
    return datetime.date(year=dt.year, month=dt.month, day=dt.day)


def get_duration(duration):
    return datetime.timedelta(**duration)


################################################################################
## ERRORS


class HarmonySyntaxError(ValueError):
    '''Raised by the parser when an unexpected token is encountered.'''
    def __init__(self, found, expected):
        super(HarmonySyntaxError, self).__init__(
                "Invalid symbol: '{}', expected {}".format(found, expected))


class HarmonyEOLError(HarmonySyntaxError):
    '''Raised by the parser when an unexpected EOL is encountered.'''
    def __init__(self):
        super(HarmonyEOLError, self).__init__('Unexpected end of line found')


class HarmonyInitialTokenMissingError(HarmonySyntaxError):
    '''Raised only when the inital token in a clause is missing. In these cases,
    the caller of the function that raised the exception may permit the use to
    omit the clause.'''
    pass
