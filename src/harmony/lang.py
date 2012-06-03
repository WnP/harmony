'''
Cute little pidgin SQL for doing things with Harmony.
'''


import datetime
import logging
import re
import shlex

from pytz import timezone


log = logging.getLogger('lang')


AT = re.compile('AT', flags=re.IGNORECASE)
CREATE = re.compile('CREATE', flags=re.IGNORECASE)
CALENDAR = re.compile('CALENDAR', flags=re.IGNORECASE)
EVENT = re.compile('EVENT', flags=re.IGNORECASE)
FOR = re.compile('FOR', flags=re.IGNORECASE)
FROM = re.compile('FROM', flags=re.IGNORECASE)
IN = re.compile('IN', flags=re.IGNORECASE)
ON = re.compile('ON', flags=re.IGNORECASE)
TIMEZONE = re.compile('TIMEZONE', flags=re.IGNORECASE)
UNTIL = re.compile('UNTIL', flags=re.IGNORECASE)

DAYS = re.compile('DAYS?', flags=re.IGNORECASE)
HOURS = re.compile('HOURS?', flags=re.IGNORECASE)
MINUTES = re.compile('MINUTES?', flags=re.IGNORECASE)
WEEKS = re.compile('WEEKS?', flags=re.IGNORECASE)
TIME_SYMBOLS = (DAYS, HOURS, MINUTES, WEEKS)

LITERAL = re.compile('\w+', flags=re.IGNORECASE)
NUMBER = re.compile('\d+(\.\d*)?', flags=re.IGNORECASE)


class HarmonyEOLError(ValueError):
    def __init__(self):
        super(HarmonyEOLError, self).__init__('Unexpected end of line found')


class HarmonySyntaxError(ValueError):
    def __init__(self, found, expected):
        super(HarmonySyntaxError, self).__init__(
                "Invalid symbol: '{}', expected {}".format(found, expected))


################################################################################
## PARSER


def parse_line(syms):
    log.debug('parse line')
    if accept(CREATE, syms):
        stmt = parse_create_stmt(syms)
    expect_eof(syms)
    return stmt


def parse_create_stmt(syms):
    log.debug('parse create')
    if accept(CALENDAR, syms):
        return parse_create_calendar_stmt(syms)
    elif accept(EVENT, syms):
        return parse_create_event_stmt(syms)


def parse_create_calendar_stmt(syms):
    log.debug('parse create calendar')
    cal_parts = {}
    if expect_peek(LITERAL, syms):
        cal_parts['name'] = syms.pop(0)
    parse_in_timezone_clause(syms, cal_parts)
    return cal_parts


def parse_create_event_stmt(syms):
    log.debug('parse create event')
    event_parts = {}
    if expect_peek(LITERAL, syms):
        event_parts['name'] = syms.pop(0)
    expect(IN, syms)
    expect(CALENDAR, syms)
    if expect_peek(LITERAL, syms):
        event_parts['calendar'] = syms.pop(0)
    if expect(FROM, syms):
        event_parts['from'] = parse_time_clause(syms)
    if accept(UNTIL, syms):
        event_parts['until'] = parse_time_clause(syms)
    elif accept(FOR, syms):
        event_parts['for'] = parse_duration_clause(syms)
    else:
        error(syms, '{0.pattern} or {1.pattern}'.format(UNTIL, FOR))
    return event_parts


def parse_time_clause(syms):
    log.debug('parse time clause')
    time_parts = {}
    initial_literal = None
    if expect_peek(LITERAL, syms):
        initial_literal = syms.pop(0)
    if accept(AT, syms):
        time_parts['date'] = initial_literal
        if expect_peek(LITERAL, syms):
            time_parts['time'] = syms.pop(0)
            parse_in_timezone_clause(syms, time_parts)
    else:
        time_parts['time'] = initial_literal
        parse_in_timezone_clause(syms, time_parts)
        if accept(ON, syms):
            if expect_peek(LITERAL, syms):
                time_parts['date'] = syms.pop(0)
    return time_parts


def parse_in_timezone_clause(syms, output_dict):
    log.debug('parse in timezone clause')
    if not accept(IN, syms):
        return
    expect(TIMEZONE, syms)
    if expect_peek(LITERAL, syms):
        output_dict['timezone'] = syms.pop(0)


def parse_duration_clause(syms):
    log.debug('parse duration clause')
    duration_parts = {}
    while peek(NUMBER, syms):
        num = float(syms.pop(0))
        for tsym in TIME_SYMBOLS:
            if peek(tsym, syms):
                duration_parts[syms.pop(0).lower()] = num
                break
        else:
            error(syms, ' or '.join([tsym.pattern for tsym in TIME_SYMBOLS]))
    return duration_parts


def accept(target, syms, pop=True):
    log.debug('will accept: {}'.format(target.pattern))
    try:
        does_match = target.match(syms[0]) is not None
    except IndexError:
        log.debug('found eof')
        return False
    if does_match:
        log.debug("accepted '{}'".format(syms[0]))
        if pop:
            syms.pop(0)
        return True
    else:
        log.debug("refused '{}'".format(syms[0]))
        return False


def peek(target, syms):
    log.debug("peeking for '{}'".format(target.pattern))
    return accept(target, syms, pop=False)


def expect(target, syms):
    log.debug("expecting '{}'".format(target.pattern))
    if accept(target, syms):
        return True
    error(syms, target.pattern)


def expect_peek(target, syms):
    log.debug("expecting '{}'".format(target.pattern))
    if peek(target, syms):
        return True
    error(syms, target.pattern)


def expect_eof(syms):
    log.debug('expecting eof')
    if len(syms) > 0:
        raise HarmonySyntaxError(syms[0], 'end of line')


def error(syms, expected):
    try:
        raise HarmonySyntaxError(syms[0], expected)
    except IndexError:
        raise HarmonyEOLError()


################################################################################
## SEMANTIC ANALYZER


DATE_FMTS = ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y')
TIME_FMTS = ('%H:%M',)


def get_datetime(datetime_string, fmts):
    for fmt in fmts:
        try:
            return datetime.datetime.strptime(datetime_string, fmt)
        except ValueError:
            pass
    raise ValueError('Invalid datetime string: {}'.format(datetime_string))


def get_time(time_string, tz=None):
    dt = get_datetime(time_string, TIME_FMTS)
    if tz is None:
        return datetime.time(hour=dt.hour, minute=dt.minute)
    else:
        return datetime.time(hour=dt.hour, minute=dt.minute,
                             tzinfo=timezone(tz))


def get_date(date_string):
    dt = get_datetime(date_string, DATE_FMTS)
    return datetime.date(year=dt.year, month=dt.month, day=dt.day)


def analyze_new_event(event):
    if 'from' in event:
        event['from'] = analyze_datetime(event['from'])
    if 'until' in event:
        event['until'] = analyze_datetime(event['until'])
    if 'for' in event:
        event['for'] = analyze_duration(event['for'])


def analyze_datetime(dt_dict):
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


def analyze_duration(duration):
    return datetime.timedelta(**duration)
