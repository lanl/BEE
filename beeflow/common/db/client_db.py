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
        result = bdb.getone(self.db_file, stmt)[0]
        hostname = result
        return hostname


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
                        hostname TEXT);"""
        if not bdb.table_exists(self.db_file, 'info'):
            bdb.create_table(self.db_file, info_stmt)
            # insert a new workflow into the database
            stmt = """INSERT INTO info (hostname) VALUES(?);"""
            tmp = ""
            bdb.run(self.db_file, stmt, [tmp])

    @property
    def info(self):
        """Get info from the database."""
        return ClientInfo(self.db_file)


def open_db(db_file):
    """Open and return a new database."""
    return ClientDB(db_file)
