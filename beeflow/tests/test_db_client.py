"""Tests of the client database."""
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

    assert len(list(db.info)) == 0


def test_info(temp_db):
    """Test setting the info."""
    db = temp_db

    db.info.set_hostname('front_end_name')
    assert db.info.get_hostname == 'front_end_name'
