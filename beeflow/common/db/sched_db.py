"""Scheduler database code."""

import jsonpickle
from beeflow.common.db import bdb


class Resources:
    """Resources wrapper class."""

    def __init__(self, db_file):
        """Create the resources class."""
        self.db_file = db_file

    def __iter__(self):
        """Create an iterator over the resources."""
        stmt = 'SELECT id, resource FROM resources'
        result = bdb.getall(self.db_file, stmt)
        for rslt in result:
            resource = jsonpickle.decode(rslt[1])
            yield resource

    def extend(self, resources):
        """Add a list of new resources."""
        for resource in resources:
            data = jsonpickle.encode(resource)
            stmt = 'INSERT INTO resources (resource) VALUES (?)'
            bdb.run(self.db_file, stmt, [data])

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
        resource_stmt = """CREATE TABLE IF NOT EXISTS resources(
                        id INTEGER PRIMARY KEY ASC,
                        resource TEXT);"""
        bdb.create_table(self.db_file, resource_stmt)

    @property
    def resources(self):
        """Get resources from the database."""
        return Resources(self.db_file)


def open_db(db_file):
    """Open and return a new database."""
    return SchedDB(db_file)
