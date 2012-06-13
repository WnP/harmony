'''
Model layer. Provides the infrastructure for defining models and fields and
converting Python data to SQLite data.
'''

from types import FunctionType

from datetime import datetime
from pytz import timezone as pytz_timezone

from . import db


class Field(object):
    '''Generic database field.'''

    def __init__(self, primary_key=False, unique=False, null=False,
                 default=None):
        self.primary_key = primary_key
        self.null = null
        self.default = default
        self.unique = unique

    def to_sql(self, value):
        '''Convert {value} into a representation that can be plugged into a
        SQL query. This method should probably be overridden by subclasses.

        @param value: Value to transform (object)
        @returns: The transformed value (object)
        '''
        if value is None:
            return u'null'
        return self.adapt(value)

    def adapt(self, value):
        '''A SQLite adapter function to convert {value} to a SQLite type. This
        method should not be overridden by subclasses; instead, write an _adapt
        method that this method will call, if it exists.

        @param value: Value to adapt (object)
        @returns: A unicode string representation of the object (unicode)
        '''
        if hasattr(self, '_adapt'):
            return self._adapt(value)
        return unicode(value)

    def convert(self, value):
        '''A SQLite converter function to convert {value} from a string
        (produced by the sqlite3 module) to a Python type. This method should
        not be overridden by subclasses; instead, write a _convert method that
        this method will call, if it exists.

        @param value: Value to convert (str)
        @returns: A Python object (object)
        '''
        if value is 'null':
            return None
        if hasattr(self, value):
            return self._convert(value)
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

    def _adapt(self, value):
        return unicode(int(value))

    def _convert(self, value):
        return int(value)


class BooleanField(IntegerField):
    '''A boolean field. Stored as an INTEGER in SQLite.'''

    column_type = 'boolean'

    YES_STR_VALUES = ('yes', 'true', '1')
    NO_STR_VALUES = ('no', 'false', '0')

    def _adapt(self, value):
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
        return super(BooleanField, self)._adapt(bool_value)

    def _convert(self, value):
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

    def to_sql(self, value):
        return u"'{}'".format(self.adapt(value))

    def _adapt(self, value):
        return unicode(value)

    def _convert(self, value):
        return unicode(value)


class TimezoneField(TextField):
    '''Stores a timezone.'''

    column_type = 'TEXT'

    # TODO: Create mapping of system timezone values ('PDT', 'PST', etc) to
    # tzinfo.

    def convert(self, value):
        return pytz_timezone(value)


class DateTimeField(Field):
    '''Stores a datetime object.'''

    column_type = 'TEXT'

    STORAGE_FORMAT = '%Y-%m-%d %H:%M:%s%z'

    def _adapt(self, value):
        # The isoformat conversion is equivalent to str(value), but I wanted to
        # be explicit.
        return unicode(value.strptime(DateTimeField.STORAGE_FORMAT))

    def _convert(self, value):
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


class ModelOptions(object):
    def __init__(self):
        self.table = ''
        self.fields = {}


class ModelMeta(type):
    '''Builds models, the way metaclasses do.'''

    def __new__(cls, name, bases, attrs):
        # Only do this for subclasses, not for the Model superclass itself
        parents = [b for b in bases if isinstance(b, ModelMeta)]
        if not parents:
            return super(ModelMeta, cls).__new__(cls, name, bases, attrs)

        new_class = super(ModelMeta, cls).__new__(cls, name, bases, attrs)
        # Add a primary key field
        attrs['id'] = IntegerField(primary_key=True)
        opts = ModelOptions()
        opts.table = name.lower()
        for name, value in attrs.items():
            if not isinstance(value, Field):
                continue
            new_class.process_field(name, value, attrs, opts)
        attrs['_meta'] = opts
        return type.__new__(cls, name, bases, attrs)

    def process_field(cls, name, field, attrs, opts):
        opts.fields[name] = field
        attrs[name] = None


class Model(object):
    '''Generic model. This is the thing (and its subclasses) that will be
    committed to a backing store of some kind.'''

    __metaclass__ = ModelMeta

    def __repr__(self):
        return "<{0.__class__.__name__} '{0!s}'>".format(self)

    def __str__(self):
        return str(unicode(self))

    def save(self):
        table = self._meta.table
        fields = {}
        for name, field in self._meta.fields.items():
            field_value = getattr(self, name)
            if field_value is None:
                field_value = field.default
            if isinstance(field, ForeignKeyField) and field_value is not None:
                field_value = field_value.id
            fields[name] = field.to_sql(field_value)

        # INSERT or UPDATE; algorithm copied from Django
        # If id is not None, do a SELECT to see if the record exists. If so, do
        # an UPDATE. Otherwise, do an INSERT.
        if self.id is not None:
            id_sql = fields['id']
            rows = db.db.select(table, {'id': id_sql})
            if len(rows) > 0:
                db.db.update(table, fields, {'id': id_sql})
                return
        db.db.insert(table, fields)
