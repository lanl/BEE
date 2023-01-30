"""Scheduler database code."""
from contextlib import contextmanager
import sqlite3
import jsonpickle

import bdb

class Resources:
    """Resources wrapper class."""

    def __init__(self, db_file):
        """Create the resources class."""
        self.db_file = db_file

    def __iter__(self):
        """Create an iterator over the resources."""
        stmt = 'SELECT id, resource FROM resources'
        while True:
            item = bdb.getone(self.db_file, stmt)
            if item is None:
                break
            resource = jsonpickle.decode(item['resource'])
            yield resource

    def extend(self, resources):
        """Add a list of new resources."""
        for resource in resources:
            data = jsonpickle.encode(resource)
            bdb.run(self.db_file, 'INSERT INTO resources (resource) VALUES (:?)', [data])
        #self._conn.commit()

    def clear(self):
        """Remove all resources."""
        clear_stmt = 'DELETE FROM resources'
        bdb.run(self.db_file, clear_stmt)


class SchedDB:
    """Scheduler database."""

    def __init__(self, db_file):
        """Construct a new scheduler database connection."""
        self.db_file = db_file
        self._init_tables()

    def _init_tables(self):
        """Initialze the scheduler tables if they don't exist."""
        resource_stmt= """CREATE TABLE IF NOT EXISTS resources(
                        id INTEGER PRIMARY KEY ASC,
                        resource TEXT);"""
        bdb.create_table(self.db_file, resource_stmt)

    @property
    def resources(self):
        """Get resources from the database."""
        return Resources(self.db_file)


@contextmanager
def open_db(fname):
    """Open and return a new database."""
    with sqlite3.connect(fname) as conn:
        conn.row_factory = sqlite3.Row
        yield SchedDB(conn)
