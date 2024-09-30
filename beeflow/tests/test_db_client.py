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

    hn = db.info.get_hostname()
    assert hn == ""


def test_info(temp_db):
    """Test setting the info."""
    db = temp_db

    db.info.set_hostname('front_end_name')
    hn = db.info.get_hostname()

    print("testing get_info: ", db.info.get_info())
    assert hn == 'front_end_name'
