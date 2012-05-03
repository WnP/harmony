import re

def _c(pattern, flags=re.U):
    return re.compile(pattern, flags=flags)

CR = '\r'
LF = '\n'
CRLF = _c('(?:{}{})'.format(CR, LF))

# Space and tab
_WSP = '\x20\t'
WSP = _c('[{}]'.format(_WSP))

_DQUOTE = '"'
DQUOTE = _c('[{}]'.format(_DQUOTE))

_DIGIT_RANGE = '0-9'
DIGIT = _c('[{}]'.format(_DIGIT_RANGE))

_ALPHA_RANGE = 'A-Za-z'
ALPHA = _c('[{}]'.format(_ALPHA_RANGE))

# Control characters
_CTL = ('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11'
        '\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1F\x7F')
CTL = _c('[{}]'.format(_CTL))

# All textual/printable characters
VALUE_CHAR = _c('[^{}]'.format(_CTL))
# All characters except controls, and ":;,
SAFE_CHAR = _c('[^{}{};:,]'.format(_CTL, _DQUOTE), flags=re.U)
# Characters safe for quoted strings, everything above and including :;,
QSAFE_CHAR = _c('[^{}{}]'.format(_CTL, _DQUOTE))

# String in quotes
QUOTED_STRING = _c('{0}{1.pattern}*{0}'.format(_DQUOTE, QSAFE_CHAR))
VALUE = _c('{0.pattern}*'.format(VALUE_CHAR))

IANA_TOKEN = _c('[-{0}{1}]+'.format(_ALPHA_RANGE, _DIGIT_RANGE))
VENDORID = _c('[{0}{1}]{2}'.format(_ALPHA_RANGE, _DIGIT_RANGE, '{3,}'))
XNAME = _c('X-{0.pattern}-[{1}{2}-]+'.format(VENDORID, _ALPHA_RANGE,
                                             _DIGIT_RANGE))

PARAM_TEXT = _c('{0.pattern}*'.format(SAFE_CHAR))
PARAM_VALUE = _c('(?:{0.pattern}|{1.pattern})'.format(PARAM_TEXT,
                                                      QUOTED_STRING))
PARAM_NAME = _c('(?:{0.pattern}|{1.pattern})'.format(IANA_TOKEN, XNAME))
PARAM = _c('{0.pattern}={1.pattern}(?:,{1.pattern})*'.format(PARAM_NAME,
                                                             PARAM_VALUE))

NAME = _c('(?:{0.pattern}|{1.pattern})'.format(IANA_TOKEN, XNAME))

# Line folds are CRLF followed by whitespace
FOLD_MARKER = _c('{0}{1}{2}'.format(CR, LF, _WSP))

CONTENT_LINE = _c('''^(?P<name>{name.pattern})
                      (?P<params>(?:;{param.pattern})*):
                      (?P<value>{value.pattern})
                      (?:{crlf.pattern})?$'''.format(
                          name=NAME,
                          param=PARAM,
                          value=VALUE,
                          crlf=CRLF),
                      flags=re.U|re.X)
