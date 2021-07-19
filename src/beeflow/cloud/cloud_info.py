
"""CloudInfo class code."""

import json
import os
import sys


# TODO: Add unit tests for CloudInfo


class CloudInfoError(Exception):
    """Error class raised by the CloudInfo class."""

    def __init__(self, msg):
        """Cloud info error constructor."""
        self.msg = msg


class CloudInfo:
    """This wraps a secondary set up file that stores conf information."""

    def __init__(self, fname):
        """Cloud info constructor."""
        self._fname = fname
        self._data = None

    def save(self):
        """Save the Cloud Info file."""
        if self._data is not None:
            with open(self._fname, 'w') as fp:
                json.dump(self._data, fp=fp, indent=4)

    def set(self, key, value):
        """Set the value of a key."""
        self._load()
        if key in self._data:
            print('Overwriting CloudInfo key', key, file=sys.stderr)
        self._data[key] = value

    def get(self, key):
        """Get the value of a key."""
        self._load()
        try:
            return self._data[key]
        except KeyError:
            raise CloudInfoError('Missing data from the CloudInfo file. You may have skipped a step in the cloud setup')

    def _load(self):
        """Load data from the file."""
        if self._data is None:
            if os.path.exists(self._fname):
                with open(self._fname) as fp:
                    self._data = json.load(fp)
            else:
                self._data = {}
