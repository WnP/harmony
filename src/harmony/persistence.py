'''
Harmony stores all its calendar and event data in a SQLite database. This module
handles that stuff.
'''


# Database singleton instance
db = None


class EventSQLiteOptions(object):
    table = 'event'

    fields = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'summary': "TEXT NOT NULL DEFAULT ''",
        'start': 'TEXT NOT NULL',
        'end': 'TEXT NOT NULL',
        'start_timezone': "timezone NOT NULL DEFAULT ''",
        'end_timezone': "timezone NOT NULL DEFAULT ''",
        'all_day': 'INTEGER NOT NULL DEFAULT 0',
        'calendar': 'INTEGER REFERENCES "calendar"("id")',
    }


class CalendarSQLiteOptions(object):
    table = 'calendar'

    fields = {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'name': 'TEXT UNIQUE NOT NULL',
        'timezone': "timezone NOT NULL DEFAULT ''",
        'is_default': 'INTEGER NOT NULL DEFAULT 0',
    }




################################################################################
## LOW LEVEL PERSISTENCE


def initialize_sqlite(dbpath):
    '''Create a database instance and connect to the specified file.

    @param dbpath: Path to a SQLite database file. (str)
    '''
    global db
    db = SQLiteDatabase()
    db.connect(dbpath)


class SQLiteDatabase(object):
    '''SQLite storage bridge.'''

    OPERATORS = {
        None: '=',
        'eq': '=',
        'lt': '<',
        'le': '<=',
        'gt': '>',
        'ge': '>=',
        'ne': '!=',
    }

    def __init__(self):
        self.db = None

    def connect(dbpath):
        '''Connect to a SQLite database.

        @param dbpath: Path to a SQLite file. (str)
        '''
        import sqlite3
        self.db = sqlite3.connect(dbpath)


    def _execute(sql, values=None):
        '''Execute a SQL query. SQL should use qmark or :keyword style, and
        provide its values as either a list or dict.

        @param sql: The SQL to execute. (str)
        @param values: Values to pass to execute() for the db engine to fill
        into ? or :keyword placeholders. (list or dict)
        @returns: Database cursor. (db.Cursor)
        '''
        if self.db is None:
            raise ValueError('Connect to database before issuing a query')
        args = [sql]
        if values is not None:
            args.append(values)
        return self.db.execute(*args)


    def _build_binary_expn(field_and_operator):
        '''Build a qmark'd binary expression.

        The incoming {field_and_operator} argument should be a column name with
        an optional operator separated by '__'. The operator should be one of
        the keys of the OPERATORS dictionary in this module. If the operator is
        omitted, it is assumed to be equals.

        @param field_and_operator: Column name and optional operator. (str)
        @returns: A SQL expression with a qmark on the RHS. (str)
        '''
        try:
            field, operator = field_and_operator.split('__')
        except ValueError:
            field = field_and_operator
            operator = None
        return '"{}" {} ?'.format(field, OPERATORS[operator])


    def _build_where_clause(criteria_keys):
        '''Build a WHERE clause.

        The incoming {criteria_keys} argument should be a list of
        field__operator strings to be passed to _build_binary_expn. These
        expressions will be AND'd together.

        @param criteria_keys: List of field__operator strings with which to
        build a WHERE clause. (list)
        @returns: The WHERE clause. (str)
        '''
        criteria_expns = [_build_binary_expn(fo) for fo in criteria_keys]
        return 'WHERE {}'.format(' AND '.join(criteria_expns))


    def create_table(table, columns, create_if_not_exists=True):
        '''Build and execute a CREATE TABLE query.

        @param table: Table name. (str)
        @param columns: A mapping of column names to SQLite column type
        definitions. (dict)
        @param create_if_not_exists: If True, execute the CREATE statement with
        IF NOT EXISTS, which will avoid raising an error if the table already
        exists. (bool)
        '''
        sql = 'CREATE TABLE{if_not_exists} "{table}"'.format(
                if_not_exists=' IF NOT EXISTS' if create_if_not_exists else '',
                table=table)

        column_specs = []
        for col, spec in columns.items():
            column_specs.append('"{name}" {spec}'.format(col, spec))
        sql += '({})'.format(', '.join(column_specs))

        _execute(sql)


    def insert(table, values):
        '''Build and execute an INSERT query.

        @param table: Table name. (str)
        @param values: Mapping of columns to values to insert. (dict)
        @returns: True if row count >= 0. (I think this counts as a rough
        indication of whether the query succeeded or not.) (bool)
        '''
        sql = 'INSERT INTO "{table}" ({columns}) VALUES ({values})'.format(
            table=table,
            columns=', '.join(['"{}"'.format(c) for c in values.keys()]),
            values=', '.join('?' * len(values))
        )
        return _execute(sql, values.values()).rowcount > 0


    def select(table, criteria=None):
        '''Build and execute a SELECT query.

        @param table: Table name. (str)
        @param criteria: Argument to pass to _build_where_clause. See that
        function's docstring for details. (dict)
        @returns: A list of dictionaries, one per row, that map field names to
        values. (list of dict)
        '''
        sql = 'SELECT * FROM "{table}"'.format(table=table)
        values = None

        if criteria is not None:
            fields, values = zip(*criteria.items())
            sql += ' {}'.format(_build_where_clause(criteria))

        cur = _execute(sql, values)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


    def update(table, values, criteria=None):
        '''Build and execute an UPDATE query.

        @param table: Table name. (str)
        @param values: Mapping of columns to values to update. (dict)
        @param criteria: Argument to pass to _build_where_clause. (See that
        function's docstring for details.) (dict)
        @returns: The number of rows updated. (int)
        '''
        sql = 'UPDATE "{table}"'.format(table=table)
        fields, qmark_values = zip(*values.items())

        set_expns = [_build_binary_expn(f) for f in fields]
        sql += ' SET {}'.format(', '.join(set_expns))

        if criteria is not None:
            fields, cvalues = zip(*criteria.items())
            sql += ' {}'.format(_build_where_clause(fields))
            qmark_values = qmark_values + cvalues

        return _execute(sql, qmark_values).rowcount


    def delete(table, criteria=None):
        '''Build and execute a DELETE query.

        Be careful! If you don't give this function a value for the {criteria},
        you will delete all the rows in {table}!

        @param table: Table name. (str)
        @param criteria: Argument to pass to _build_where_clause. (See that
        function's docstring for details.) (dict)
        @returns: The number of rows deleted. (int)
        '''
        sql = 'DELETE FROM "{table}"'.format(table=table)
        values = None

        if criteria is not None:
            fields, values = zip(*criteria.items())
            sql += ' {}'.format(_build_where_clause(fields))

        return _execute(sql, values).rowcount
