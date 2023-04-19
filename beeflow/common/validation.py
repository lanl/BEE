"""Specialized functions for validation and config initialization."""
import os
from pathlib import Path


def validate_path(path):
    """Check that the path exists."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        raise ValueError(f'path "{path}" does not exist')
    return path


def dir_(path):
    """Check that the path exists and is a directory."""
    path = validate_path(path)
    if not os.path.isdir(path):
        raise ValueError('path "{path}" is not a directory')
    return path


def make_dir(path):
    """Check if the dir exists and if not create it."""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def parent_dir(path):
    """Ensure that the parent dir of path exists, or create it."""
    make_dir(Path(path).parent)
    return path


def file_(path):
    """Check that the path exists and is a file."""
    path = validate_path(path)
    if not os.path.isfile(path):
        raise ValueError(f'path "{path}" is not a file')
    return path


def nonnegative_int(value):
    """Validate that the input is nonnegative."""
    i = int(value)
    if i < 0:
        raise ValueError('the value must be nonnegative')
    return i


# NOTE: You must use validate_bool for all boolean values (since just using
#       bool, as in bool('False'), gives True for any string of length > 0)
def bool_(value):
    """Validate a boolean value."""
    return str(value).lower() == 'true'


def time_limit(value):
    """Validate a time limit entry."""
    value = value.strip()
    if not value:
        return ''
    _ = [int(part) for part in value.split(':')]
    return value
