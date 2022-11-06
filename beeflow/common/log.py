"""Logging interface for BEE."""
import logging
import os


# Set the default log level (BEE_LOG_LEVEL will be passed in by beeflow/cli.py)
LEVEL = os.getenv('BEE_LOG_LEVEL')
LEVEL = 'DEBUG' if LEVEL is None else LEVEL


def setup(name):
    """Set up and return logger.

    :param name: Name to be used for logger (best would be __name__)
    :type level: String
    """
    log = logging.getLogger(name)
    log.setLevel(LEVEL)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(name)s:%(funcName)s(): %(msg)s'))
    log.addHandler(handler)
    return log
