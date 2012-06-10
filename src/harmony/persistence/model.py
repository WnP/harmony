'''
Model layer. Provides the infrastructure for defining models and fields and
converting Python data to SQLite data.
'''


from datetime import datetime
from pytz import timezone as pytz_timezone


class Field(object):
    '''Generic database field.'''

    def __init__(self, primary_key=False, unique=False, null=False,
                 default=None):
        self.primary_key = primary_key
        self.null = null
        self.default = default
        self.unique = unique

    @classmethod
    def to_sql(self, value):
        '''Convert {value} into a representation that can be plugged into a
        SQL query. This method should probably be overridden by subclasses.

        @param value: Value to transform (object)
        @returns: The transformed value (object)
        '''
        return self.adapt(value)

    @classmethod
    def adapt(self, value):
        '''A SQLite adapter function to convert {value} to a SQLite type. This
        method shoud probably be overridden by subclasses.

        @param value: Value to adapt (object)
        @returns: A unicode string representation of the object (unicode)
        '''
        return unicode(value)

    @classmethod
    def convert(self, value):
        '''A SQLite converter function to convert {value} from a string
        (produced by the sqlite3 module) to a Python type. This method shoud
        probably be overridden by subclasses.

        @param value: Value to convert (str)
        @returns: A Python object (object)
        '''
        return unicode(value)

    @property
    def column_spec(self):
        constraints = []

        if self.primary_key:
            # Setting primary_key trumps all
            return 'PRIMARY KEY AUTOINCREMENT'

        if self.unique:
            constraints.append('UNIQUE')
        if not self.null:
            constraints.append('NOT NULL')
        if self.default is not None:
            constraints.append('DEFAULT {}'.format(self.transform(self.default)))
        return '{} {}'.format(self.column_type, ' '.join(constraints))


class IntegerField(Field):
    '''An integer field.'''

    column_type = 'INTEGER'

    @classmethod
    def adapt(self, value):
        return unicode(int(value))

    @classmethod
    def convert(self, value):
        return int(value)


class BooleanField(IntegerField):
    '''A boolean field. Stored as an INTEGER in SQLite.'''

    column_type = 'boolean'

    YES_STR_VALUES = ('yes', 'true', '1')
    NO_STR_VALUES = ('no', 'false', '0')

    @classmethod
    def adapt(self, value):
        if isinstance(value, basestring):
            value = value.lower()
            # {YES,NO}_STR_VALUES are the accepted true and false values for
            # strings. Any other string values will be interpreted according to
            # how Python treats truthiness of strings
            if value in BooleanField.YES_STR_VALUES:
                value = True
            elif value in BooleanField.NO_STR_VALUES:
                value = False
        if value:
            bool_value = 1
        else:
            bool_value = 0
        return super(BooleanField, self).adapt(bool_value)

    @classmethod
    def convert(self, value):
        if isinstance(value, basestring):
            if value in YES_STR_VALUES:
                return True
            elif value in NO_STR_VALUES:
                return False
        return bool(value)


class TextField(Field):
    '''A string field.'''

    column_type = 'TEXT'

    def __init__(self, **kwargs):
        super(TextField, self).__init__(**kwargs)
        if self.default is None and not self.null:
            self.default = ''

    @classmethod
    def to_sql(self, value):
        return u"'{}'".format(self.adapt(value))

    @classmethod
    def adapt(self, value):
        return unicode(value)

    @classmethod
    def convert(self, value):
        return unicode(value)


class TimezoneField(TextField):
    '''Stores a timezone.'''

    column_type = 'TEXT'

    # TODO: Create mapping of system timezone values ('PDT', 'PST', etc) to
    # tzinfo.

    @classmethod
    def convert(self, value):
        return pytz_timezone(value)


class DateTimeField(Field):
    '''Stores a datetime object.'''

    column_type = 'TEXT'

    STORAGE_FORMAT = '%Y-%m-%d %H:%M:%s%z'

    @classmethod
    def adapt(self, value):
        # The isoformat conversion is equivalent to str(value), but I wanted to
        # be explicit.
        return unicode(value.strptime(DateTimeField.STORAGE_FORMAT))

    @classmethod
    def convert(self, value):
        return datetime.strftime(value, DateTimeField.STORAGE_FORMAT)


class ForeignKeyField(IntegerField):
    '''Foreign key/reference field.'''

    def __init__(self, referenced_model, **kwargs):
        '''
        @param referenced_model: The model class this field points to (type)
        '''
        super(ForeignKeyField, self).__init__(**kwargs)
        self.reference = referenced_model

    @property
    def column_spec(self):
        spec = super(ForeignKeyField, self).column_spec
        return '{} REFERENCES "{}"'.format(spec, self.reference._meta.table)


class ModelMetaOptions(object):
    def __init__(self):
        self.table = ''
        self.fields = {}


class ModelMeta(type):
    '''Builds models, the way metaclasses do.'''

    def __new__(meta, name, bases, attrs):
        metaopts = ModelMetaOptions()
        # Only do this for subclasses, not for the Model superclass itself
        if name != 'Model':
            attrs['id'] = IntegerField(primary_key=True)
            metaopts.table = name.lower()
            for attr, value in attrs.items():
                if not isinstance(value, Field):
                    continue
                self.process_field(attr, value, attrs, metaopts)
        attrs['_meta'] = metaopts
        return type.__new__(meta, name, bases, attrs)

    def process_field(self, name, field, attrs, meta):
        if isinstance(value, ForeignKeyField):
            self.process_foreign_key(key, value, attrs, metaopts)
        else:
            meta.fields[name] = field
            attrs[name] = None

    def process_foreign_key(self, name, field, attrs, meta):
        # TODO: Work this out.
        meta.fields[name + '_id'] = field
        attrs[name] = None


class Model(object):
    '''Generic model. This is the thing (and its subclasses) that will be
    committed to a backing store of some kind.'''

    __metaclass__ = ModelMeta

    def __repr__(self):
        return "<{0.__class__.__name__} '{0!s}'>".format(self)

    def __str__(self):
        return str(unicode(self))
