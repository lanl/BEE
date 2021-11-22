
"""BEE Cloud class."""

import base64


class CloudError(Exception):
    """Cloud error class."""

    def __init__(self, msg):
        """Cloud error constructor."""
        self.msg = msg
