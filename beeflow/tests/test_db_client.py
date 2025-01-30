"""Tests of the client database."""

# Disable W0621: Pylint complains about redefining 'temp_db' from the outer
#               scope. This is how pytest fixtures work.
# pylint:disable=W0621

import tempfile
import os

import pytest

from beeflow.common.db import client_db


@pytest.fixture
def temp_db():
    """Create a fixture for making a temporary database."""
    fname = tempfile.mktemp()
    db = client_db.open_db(fname)
    yield db
    os.remove(fname)


def test_empty(temp_db):
    """Test the empty database."""
    db = temp_db

    host_name = db.info.get_hostname()
    backend_stat = db.info.get_backend_status()
    assert host_name == ""
    assert backend_stat == ""


def test_info(temp_db):
    """Test setting the info."""
    db = temp_db

    db.info.set_hostname('front_end_name')
    host_name = db.info.get_hostname()

    db.info.set_backend_status('true')
    backend_stat = db.info.get_backend_status()

    assert host_name == 'front_end_name'
    assert backend_stat == 'true'
