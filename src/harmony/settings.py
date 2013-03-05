from datetime import tzinfo

from pytz import timezone as pytz_timezone


class Setting(object):
    '''A setting.'''

    def __init__(self, default=None):
        self.default = default

    def validate(self, new_value):
        return True

    def transform(self, new_value):
        return new_value


class StringSetting(Setting):
    '''A setting field to hold a string. All values are converted to unicode.'''

    def __init__(self, default=u''):
        super(StringSetting, self).__init__(default)

    def validate(self, new_value):
        return isinstance(new_value, basestring)

    def transform(self, new_value):
        return unicode(new_value)


class TimezoneSetting(StringSetting):
    '''A setting field to hold a timezone.'''

    def transform(self, new_value):
        if isinstance(new_value, tzinfo):
            return new_value
        new_value = super(TimezoneSetting, self).transform(new_value)
        return pytz_timezone(new_value)


class BooleanSetting(Setting):
    '''A boolean value.'''

    YES_VALUES = ('yes', 'true', '1', 1, True)
    NO_VALUES = ('no', 'false', '0', 0, False)

    def __init__(self, default=False):
        super(BooleanSetting, self).__init__(default)

    def validate(self, new_value):
        if isinstance(new_value, basestring):
            new_value = new_value.lower()
        return new_value in (BooleanSetting.YES_VALUES
                             + BooleanSetting.NO_VALUES)

    def transform(self, new_value):
        try:
            new_value = new_value.lower()
        except:
            pass
        if new_value in BooleanSetting.YES_VALUES:
            return True
        if new_value in BooleanSetting.NO_VALUES:
            return False
        raise ValueError('Invalid boolean value: {}'.format(new_value))


class Settings(object):
    '''
    A class to store all of the settings for the current run of Harmony.
    '''

    # The user's real name
    realname = StringSetting()
    # The user's timezone
    timezone = TimezoneSetting(default='UTC')
    # Use colors in the UI?
    color = BooleanSetting(default=True)

    def __new__(cls, *args, **kwargs):
        new_settings = super(Settings, cls).__new__(cls, *args, **kwargs)
        super(Settings, new_settings).__setattr__('_settings', {})
        for stg, desc in vars(cls).iteritems():
            if not isinstance(desc, Setting):
                continue
            new_settings._settings[stg] = desc
            setattr(new_settings, stg, desc.default)
        return new_settings

    def __setattr__(self, name, value):
        desc = self._settings[name]
        if value is None:
            value = desc.default
        if not desc.validate(value):
            raise ValueError("Invalid value for setting '{}': {}".format(name,
                                                                         value))
        super(Settings, self).__setattr__(name, desc.transform(value))


