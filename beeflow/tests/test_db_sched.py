"""Tests of the scheduler database."""
import tempfile
import os

import pytest

from beeflow.common.db import sched_db


@pytest.fixture
def temp_db():
    """Create a fixture for making a temporary datbase."""
    fname = tempfile.mktemp()
    db = sched_db.open_db(fname)
    yield db
    os.remove(fname)


def test_empty(temp_db):
    """Test the empty database."""
    db = temp_db

    assert len(list(db.resources)) == 0


def test_extend(temp_db):
    """Test setting the resources."""
    db = temp_db

    db.resources.extend([1, 2, 3])
    assert list(db.resources) == [1, 2, 3]


def test_clear(temp_db):
    """Test clearing the resources."""
    db = temp_db
    db.resources.extend([8, 9, 10, 11, 12, 13, 14])

    db.resources.clear()
    assert len(list(db.resources)) == 0
# Ignore W0621: PyLama complains about redefining 'temp_db' from the outer
#               scope. This is how pytest fixtures work.
# pylama:ignore=W0621
