"""BEE Cloud class."""


class CloudError(Exception):
    """Cloud error class."""

    def __init__(self, msg):
        """Cloud error constructor."""
        self.msg = msg
# Ignore W0231: This is a user-defined exception so the base class doesn't
#               usually need to be called.
# pylama:ignore=W0231
