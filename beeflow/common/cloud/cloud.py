"""BEE Cloud class."""


class CloudError(Exception):
    """Cloud error class."""

    def __init__(self, msg):
        """Cloud error constructor."""
        self.msg = msg
