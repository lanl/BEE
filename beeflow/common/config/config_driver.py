"""BEE configuration driver module.
"""

from configparser import ConfigParser
import os
import platform

class BeeConfig:
    """Class to manage and store all BEE configuration.

    BeeConfig.sysconfig is a ConfigParser object of system configurations.
    BeeConfig.userconfig is a ConfigParser object of user configurations.

    Configuration file locations by supported platform:
    Linux:
      sysconfig_file = '/etc/beeflow/bee.conf'
      userconfig_file = '~/.config/beeflow/bee.conf'
    MacOS:
      sysconfig_file = '/Library/Application Support/beeflow/bee.conf'
      userconfig_file = '~/Library/Application Support/beeflow/bee.conf'
    Windows:
      sysconfig_file = NOT SUPPORTED. Should be windows registry.
      userconfig_file = '%APPDATA%\beeflow\bee.conf'
    """

    def __init__(self):
        """Initialize BeeConfig class. We check the platform and read in
        system and user configuration files. 
        """

        self.sysconfig = ConfigParser()
        self.userconfig = ConfigParser()
        system=platform.system()
        if system == "Linux":
            sysconfig_file = '/etc/beeflow/bee.conf'
            userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
        elif system == "Darwin":
            sysconfig_file = '/Library/Application Support/beeflow/bee.conf'
            userconfig_file = os.path.expanduser('~/Library/Application Support/beeflow/bee.conf')
        elif system == "Windows":
            sysconfig_file = ''
            userconfig_file = os.path.expandvars(r'%APPDATA%\beeflow\bee.conf')

        try:
            self.sysconfig.read_file(open(sysconfig_file))
        except FileNotFoundError:
            print("System configuration " + sysconfig_file + " not found")

        try:
            self.userconfig.read_file(open(userconfig_file))
        except FileNotFoundError:
            print("User configuration " + userconfig_file + " not found")
