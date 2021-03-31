
"""BEE Cloud class."""

import base64

import beeflow.cloud.provider as provider
import beeflow.cloud.constants as constants


class CloudError(Exception):
    """Cloud error class."""

    def __init__(self, msg):
        """Cloud error constructor."""
        self.msg = msg
