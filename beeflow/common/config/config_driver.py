"""BEE configuration driver module.
"""

from configparser import ConfigParser
import os
import platform

class BeeConfig:
    """Class to manage and store all BEE configuration.
    """

    def __init__(self):
        """Initialize BeeConfig class.
        """
        system=platform.system()
        if system == "Linux":
            config_files=['bee.conf',os.path.expanduser('~/.config/beeflow/bee.conf')]
        elif system == "Darwin":
            config_files=['bee.conf',os.path.expanduser('~/Library/Application Support/beeflow/bee.conf')]
        elif system == "Windows":
            config_files=['bee.conf',os.path.expandvars(r'%APPDATA%\beeflow\bee.conf'),os.path.expandvars(r'%LOCALAPPDATA%\beeflow\bee.conf')]
