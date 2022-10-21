"""Scheduler database code."""
from contextlib import contextmanager
import sqlite3
import jsonpickle


class Resources:
    """Resources wrapper class."""

    def __init__(self, conn):
        """Create the resources class."""
        self._conn = conn

    def __iter__(self):
        """Create an iterator over the resources."""
        cur = self._conn.cursor()
        res = cur.execute('SELECT id, resource FROM resources')
        while True:
            item = res.fetchone()
            if item is None:
                break
            resource = jsonpickle.decode(item['resource'])
            yield resource

    def extend(self, resources):
        """Add a list of new resources."""
        cur = self._conn.cursor()
        for resource in resources:
            data = jsonpickle.encode(resource)
            cur.execute('INSERT INTO resources (resource) VALUES (:resource)', {'resource': data})
        self._conn.commit()

    def clear(self):
        """Remove all resources."""
        cur = self._conn.cursor()
        cur.execute('DELETE FROM resources')
        self._conn.commit()


class SchedDB:
    """Scheduler database."""

    def __init__(self, conn):
        """Construct a new scheduler database connection."""
        self._conn = conn
        self._init_tables()

    def _init_tables(self):
        """Initialze the scheduler tables if they don't exist."""
        script = """CREATE TABLE IF NOT EXISTS resources(
                        id INTEGER PRIMARY KEY ASC,
                        resource TEXT);"""
        self._conn.executescript(script)

    @property
    def resources(self):
        """Get resources from the database."""
        return Resources(self._conn)


@contextmanager
def open_db(fname):
    """Open and return a new database."""
    with sqlite3.connect(fname) as conn:
        conn.row_factory = sqlite3.Row
        yield SchedDB(conn)
