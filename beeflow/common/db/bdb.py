"""Contains functions for managing a database for workflow and task information."""

import sqlite3
from sqlite3 import Error


def connect_db(module, db_path):
    """Return a DB object."""
    db = module.open_db(db_path)
    return db


def create_connection(db_file):
    """Create a new connection with the workflow database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as error:
        print(error)
    return conn


def create_table(db_file, stmt):
    """Create a new table in the database."""
    with create_connection(db_file) as conn:
        try:
            cursor = conn.cursor()
            cursor.execute(stmt)
        except Error as error:
            print(error)


def run(db_file, stmt, params=None):
    """Run the sql statement on the database. Doesn't return anything."""
    with create_connection(db_file) as conn:
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(stmt, params)
            else:
                cursor.execute(stmt)
            conn.commit()
        except Error as error:
            print(error)


def getone(db_file, stmt, params=None):
    """Run the sql statement on the database and return the result."""
    with create_connection(db_file) as conn:
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(stmt, params)
            else:
                cursor.execute(stmt)
            result = cursor.fetchone()
        except Error:
            result = None
        return result


def getall(db_file, stmt, params=None):
    """Run the sql statement on the database and return the result."""
    with create_connection(db_file) as conn:
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(stmt, params)
            else:
                cursor.execute(stmt)
            result = cursor.fetchall()
        except Error:
            result = None
    return result


def table_exists(db_file, table_name):
    """Return true if a table exists and false if not."""
    stmt = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
    result = getall(db_file, stmt)
    return len(result) != 0


def get_table_length(db_file, table):
    """Return the number of rows in a table."""
    stmt = f"SELECT COUNT(*) from {table}"
    result = getall(db_file, stmt)
    rows = result[0][0]
    return rows
