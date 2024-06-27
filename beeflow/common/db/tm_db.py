"""Task Manager database code."""

from collections import namedtuple
import jsonpickle

from beeflow.common.db import bdb
from beeflow.common import log as bee_logging
from beeflow.common.wf_data import TaskStateUpdate

log = bee_logging.setup(__name__)


class SubmitQueue:
    """Task Manager submit queue."""

    def __init__(self, db_file):
        """Construct a submit queue handler."""
        self.db_file = db_file
        self.Job = namedtuple("Job", "id task") #noqa Snake Case

    def __iter__(self):
        """Create an iterator for going over all elements."""
        stmt = 'SELECT task FROM submit_queue ORDER BY id ASC'
        result = bdb.getall(self.db_file, stmt)
        for rslt in result:
            task = jsonpickle.decode(rslt[0])
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
        self.Job = namedtuple("Task", "id task job_id job_state") # noqa Snake Case

    def __iter__(self):
        """Create an iterator for going over all elements in the queue."""
        stmt = 'SELECT id, task, job_id, job_state FROM job_queue ORDER BY id ASC'
        result = bdb.getall(self.db_file, stmt)
        for j in result:
            id_ = j[0]
            task = jsonpickle.decode(j[1])
            job_id = j[2]
            state = j[3]
            job = self.Job(id_, task, job_id, state)
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
        result = bdb.getone(self.db_file, stmt)
        id_ = result[0]
        task = jsonpickle.decode(result[1])
        job_id = result[2]
        state = result[3]
        job = self.Job(id_, task, job_id, state)
        bdb.run(self.db_file, 'DELETE FROM job_queue WHERE id=?', [id_])
        return job

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


class UpdateQueue:
    """Task Manager update queue."""

    def __init__(self, db_file):
        """Construct an update queue handler."""
        self.db_file = db_file

    def push(self, wf_id, task_id, job_state, task_info=None, metadata=None, output=None):
        """Push an update onto the update queue."""
        stmt = """INSERT INTO update_queue (wf_id, task_id, job_state, task_info, metadata, output)
                  VALUES (:wf_id, :task_id, :job_state, :task_info, :metadata, :output)"""
        bdb.run(self.db_file, stmt, {'wf_id': wf_id, 'task_id': task_id,
                                     'job_state': job_state,
                                     'task_info': jsonpickle.encode(task_info),
                                     'metadata': jsonpickle.encode(metadata),
                                     'output': jsonpickle.encode(output)})

    def updates(self):
        """Get a list of all updates from the update queue."""
        stmt = """SELECT wf_id, task_id, job_state, task_info, metadata, output
                  FROM update_queue ORDER BY id ASC"""
        state_updates = []
        for result in bdb.getall(self.db_file, stmt):
            wf_id, task_id, job_state, task_info, metadata, output = result
            state_updates.append(TaskStateUpdate(wf_id, task_id, job_state,
                                                 jsonpickle.decode(task_info),
                                                 jsonpickle.decode(metadata),
                                                 jsonpickle.decode(output)))
        return state_updates

    def clear(self):
        """Clear the update queue."""
        bdb.run(self.db_file, 'DELETE FROM update_queue')


class TMDB:
    """Task Manager Database."""

    def __init__(self, db_file):
        """Construct a new TM database connection."""
        self.db_file = db_file
        self._init_tables()

    def _init_tables(self):
        """Initialize the workflow tables."""
        submit_queue_stmt = """CREATE TABLE IF NOT EXISTS submit_queue(
                        id INTEGER PRIMARY KEY ASC,
                        task TEXT)"""

        job_queue_stmt = """CREATE TABLE IF NOT EXISTS job_queue(
                        id INTEGER PRIMARY KEY ASC,
                        task TEXT,
                        job_id INTEGER,
                        job_state TEXT)"""

        update_queue_stmt = """CREATE TABLE IF NOT EXISTS update_queue(
                        id INTEGER PRIMARY KEY ASC,
                        wf_id TEXT,
                        task_id TEXT,
                        job_state TEXT,
                        task_info TEXT,
                        metadata TEXT,
                        output TEXT)"""

        bdb.create_table(self.db_file, submit_queue_stmt)
        bdb.create_table(self.db_file, job_queue_stmt)
        bdb.create_table(self.db_file, update_queue_stmt)

    @property
    def submit_queue(self):
        """Return a SubmitQueue object."""
        return SubmitQueue(self.db_file)

    @property
    def job_queue(self):
        """Return a JobQueue object."""
        return JobQueue(self.db_file)

    @property
    def update_queue(self):
        """Return an UpdateQueue object."""
        return UpdateQueue(self.db_file)


def open_db(db_file):
    """Open and return a new database."""
    return TMDB(db_file)
