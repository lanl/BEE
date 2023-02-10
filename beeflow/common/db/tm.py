"""Task Manager database code."""

from collections import namedtuple
from contextlib import contextmanager
import sqlite3
import jsonpickle

from beeflow.common.db import bdb

class SubmitQueue:
    """Task Manager submit queue."""

    def __init__(self, db_file):
        """Construct a submit queue handler."""
        self.db_file = db_file
        self.Job = namedtuple("Job", "id task")

    def __iter__(self):
        """Create an iterator for going over all elements."""
        stmt = 'SELECT task FROM submit_queue ORDER BY id ASC'
        result = bdb.getall(self.db_file, stmt)
        for j in result:
            job = self.Job(*result)
            task = jsonpickle.decode(job.task)
            yield task

    def count(self):
        """Count the number of items in the submit queue."""
        stmt = 'SELECT COUNT(*) AS count FROM submit_queue'
        count = bdb.getone(self.db_file, stmt)[0]
        return count

    def push(self, task):
        """Push the task onto the submit queue."""
        task_data = jsonpickle.encode(task)
        stmt = 'INSERT INTO submit_queue (task) VALUES (?)'
        bdb.run(self.db_file, stmt, [task_data])

    def pop(self):
        """Pop the bottom element off the queue."""
        select_stmt = 'SELECT id, task FROM submit_queue ORDER BY id ASC'
        result = bdb.getone(self.db_file, select_stmt)
        job = self.Job(*result)
        id_ = job.id
        task_data = job.task
        task = jsonpickle.decode(task_data)
        delete_stmt = 'DELETE FROM submit_queue WHERE id=?'
        bdb.run(self.db_file, delete_stmt, [id_])
        return task

    def clear(self):
        """Clear the submit queue."""
        stmt = 'DELETE FROM submit_queue'
        bdb.run(self.db_file, stmt)


class JobQueue:
    """Task Manager job queue."""

    def __init__(self, db_file):
        """Construct a job queue handler."""
        self.db_file = db_file
        self.Job = namedtuple("Task", "id task job_id job_state")

    def __iter__(self):
        """Create an iterator for going over all elements in the queue."""
        stmt = 'SELECT id, task, job_id, job_state FROM job_queue ORDER BY id ASC'
        result = bdb.getall(self.db_file, stmt)
        for j in result:
            job = self.Job(*j)
            yield job

    def count(self):
        """Count the number of items in the job queue."""
        stmt = 'SELECT COUNT(*) AS count FROM job_queue'
        count = bdb.getone(self.db_file, stmt)[0]
        return count

    def push(self, task, job_id, job_state):
        """Push the job info onto the queue."""
        task_data = jsonpickle.encode(task)
        stmt = """INSERT INTO job_queue (task, job_id, job_state)
               VALUES (?, ?, ?)"""
        bdb.run(self.db_file, stmt, [task_data, job_id, job_state])

    def pop(self):
        """Pop the bottom element off the queue."""
        stmt = 'SELECT id, task, job_id, job_state FROM job_queue ORDER BY id ASC'
        job = bdb.getone(self.db_file, stmt)
        id_ = job['id']
        task = jsonpickle.decode(job['task'])
        job_id = job['job_id']
        job_state = job['job_state']
        bdb.run(self.db_file, 'DELETE FROM job_queue WHERE id=?', [id_])
        return {'task': task, 'job_id': job_id, 'job_state': job_state}

    def update_job_state(self, id_, job_state):
        """Update the job_state."""
        stmt = 'UPDATE job_queue SET job_state=? WHERE id=?'
        bdb.run(self.db_file, stmt, [job_state, id_])

    def remove_by_id(self, id_):
        """Remove a job from the queue by ID."""
        stmt = 'DELETE FROM job_queue WHERE id=?'
        bdb.run(self.db_file, stmt, [id_])

    def clear(self):
        """Clear the job queue."""
        stmt = 'DELETE FROM job_queue'
        bdb.run(self.db_file, stmt)


class TMDB:
    """Task Manager Database."""

    def __init__(self, db_file):
        """Construct a new TM database connection."""
        self.db_file = db_file
        self._init_tables()

    def _init_tables(self):
        """Initialize the workflow tables."""
        submit_queue_stmt  = """CREATE TABLE IF NOT EXISTS submit_queue(
                        id INTEGER PRIMARY KEY ASC,
                        task TEXT)"""

        job_queue_stmt = """CREATE TABLE IF NOT EXISTS job_queue(
                        id INTEGER PRIMARY KEY ASC,
                        task TEXT,
                        job_id INTEGER,
                        job_state TEXT)"""

        bdb.create_table(self.db_file, submit_queue_stmt)
        bdb.create_table(self.db_file, job_queue_stmt)

    @property
    def submit_queue(self):
        """Return a SubmitQueue object."""
        return SubmitQueue(self.db_file)

    @property
    def job_queue(self):
        """Return a JobQueue object."""
        return JobQueue(self.db_file)


@contextmanager
def open_db(db_file):
    """Open and return a new database."""
    yield TMDB(db_file)
