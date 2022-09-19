"""Task Manager database code."""
from contextlib import contextmanager
import sqlite3
import jsonpickle


class SubmitQueue:
    """Task Manager submit queue."""

    def __init__(self, conn):
        """Construct a submit queue handler."""
        self._conn = conn

    def __iter__(self):
        """Create an iterator for going over all elements."""
        cur = self._conn.cursor()
        res = cur.execute('SELECT task FROM submit_queue ORDER BY id ASC')
        while True:
            row = res.fetchone()
            if row is None:
                break
            task = jsonpickle.decode(row['task'])
            yield task

    def count(self):
        """Count the number of items in the submit queue."""
        res = self._conn.execute('SELECT COUNT(*) AS count FROM submit_queue').fetchone()
        return res['count']

    def push(self, task):
        """Push the task onto the submit queue."""
        cur = self._conn.cursor()
        task_data = jsonpickle.encode(task)
        cur.execute('INSERT INTO submit_queue (task) VALUES (:task)', {'task': task_data})
        self._conn.commit()

    def pop(self):
        """Pop the bottom element off the queue."""
        cur = self._conn.cursor()
        res = cur.execute('SELECT id, task FROM submit_queue ORDER BY id ASC').fetchone()
        id_ = res['id']
        print(id_)
        task_data = res['task']
        task = jsonpickle.decode(task_data)
        cur.execute('DELETE FROM submit_queue WHERE id = :id', {'id': id_})
        self._conn.commit()
        return task

    def clear(self):
        """Clear the submit queue."""
        self._conn.execute('DELETE FROM submit_queue')


class JobQueue:
    """Task Manager job queue."""

    def __init__(self, conn):
        """Construct a job queue handler."""
        self._conn = conn

    def __iter__(self):
        """Create an iterator for going over all elements in the queue."""
        res = self._conn.execute(
            'SELECT id, task, job_id, job_state FROM job_queue ORDER BY id ASC',
        )
        while True:
            row = res.fetchone()
            if row is None:
                break
            yield {
                'id': row['id'],
                'task': jsonpickle.decode(row['task']),
                'job_id': row['job_id'],
                'job_state': row['job_state'],
            }

    def count(self):
        """Count the number of items in the job queue."""
        res = self._conn.execute('SELECT COUNT(*) AS count FROM job_queue').fetchone()
        return res['count']

    def push(self, task, job_id, job_state):
        """Push the job info onto the queue."""
        cur = self._conn.cursor()
        task_data = jsonpickle.encode(task)
        cur.execute(
            """INSERT INTO job_queue (task, job_id, job_state)
               VALUES (:task, :job_id, :job_state)""",
            {'task': task_data, 'job_id': job_id, 'job_state': job_state},
        )
        self._conn.commit()

    def pop(self):
        """Pop the bottom element off the queue."""
        cur = self._conn.cursor()
        res = cur.execute(
            'SELECT id, task, job_id, job_state FROM job_queue ORDER BY id ASC',
        ).fetchone()
        id_ = res['id']
        task = jsonpickle.decode(res['task'])
        job_id = res['job_id']
        job_state = res['job_state']
        cur.execute('DELETE FROM job_queue WHERE id = :id', {'id': id_})
        self._conn.commit()
        return {'task': task, 'job_id': job_id, 'job_state': job_state}

    def update_job_state(self, id_, job_state):
        """Update the job_state."""
        cur = self._conn.cursor()
        cur.execute('UPDATE job_queue SET job_state = :job_state WHERE id = :id',
                    {'id': id_, 'job_state': job_state})
        self._conn.commit()

    def remove_by_id(self, id_):
        """Remove a job from the queue by ID."""
        cur = self._conn.cursor()
        cur.execute('DELETE FROM job_queue WHERE id = :id', {'id': id_})
        self._conn.commit()

    def clear(self):
        """Clear the job queue."""
        self._conn.execute('DELETE FROM job_queue')


class TMDB:
    """Task Manager Database."""

    def __init__(self, conn):
        """Construct a new TM database connection."""
        self._conn = conn
        self._init_tables()

    def _init_tables(self):
        """Initialize the workflow tables."""
        script = """CREATE TABLE IF NOT EXISTS submit_queue(
                        id INTEGER PRIMARY KEY ASC,
                        task TEXT,
                        popped INTEGER);
                    CREATE TABLE IF NOT EXISTS job_queue(
                        id INTEGER PRIMARY KEY ASC,
                        task TEXT,
                        job_id INTEGER,
                        job_state TEXT,
                        popped INTEGER);"""
        self._conn.executescript(script)

    @property
    def submit_queue(self):
        """Return a SubmitQueue object."""
        return SubmitQueue(self._conn)

    @property
    def job_queue(self):
        """Return a JobQueue object."""
        return JobQueue(self._conn)


@contextmanager
def open_db(fname):
    """Open and return a new database."""
    with sqlite3.connect(fname) as conn:
        conn.row_factory = sqlite3.Row
        yield TMDB(conn)
