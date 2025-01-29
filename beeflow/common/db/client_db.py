"""Client database code."""

from collections import namedtuple

from beeflow.common.db import bdb


class ClientInfo:
    """Client Info object."""

    def __init__(self, db_file):
        """Initialize info and db file."""
        self.Info = namedtuple("Info", "id hostname") # noqa Snake Case
        self.db_file = db_file

    def set_hostname(self, new_hostname):
        """Set hostname for current front end."""
        stmt = "UPDATE info set hostname=?"
        bdb.run(self.db_file, stmt, [new_hostname])

    def get_hostname(self):
        """Return hostname for current front end."""
        stmt = "SELECT hostname FROM info"
        hostname = bdb.getone(self.db_file, stmt)[0]
        return hostname

    def set_backend_status(self, status):
        """Set backend flag status: true (running on backend)."""
        stmt = "UPDATE info set backend=?"
        bdb.run(self.db_file, stmt, [status])

    def get_backend_status(self):
        """Return if backend flag is set to true or empty."""
        stmt = "SELECT backend FROM info"
        status = bdb.getone(self.db_file, stmt)[0]
        return status


class ClientDB:
    """Client database."""

    def __init__(self, db_file):
        """Construct a new client database connection."""
        self.db_file = db_file
        self._init_tables()

    def _init_tables(self):
        """Initialize the client table if it doesn't exist."""
        info_stmt = """CREATE TABLE IF NOT EXISTS info (
                        id INTEGER PRIMARY KEY ASC,
                        hostname TEXT,
                        backend TEXT);"""
        if not bdb.table_exists(self.db_file, 'info'):
            bdb.create_table(self.db_file, info_stmt)
            # initialize hostname and backend values
            stmt = """INSERT INTO info (hostname, backend) VALUES(?,?);"""
            bdb.run(self.db_file, stmt, ["", ""])

    @property
    def info(self):
        """Get info from the database."""
        return ClientInfo(self.db_file)


def open_db(db_file):
    """Open and return a new database."""
    return ClientDB(db_file)
