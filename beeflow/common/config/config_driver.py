"""BEE configuration driver module."""

from configparser import ConfigParser
import os
import platform


class BeeConfig:
    r"""Class to manage and store all BEE configuration.

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
        """Initialize BeeConfig class.

        We check the platform and read in system and user configuration files.
        If the user configuration file doesn't exist we create it with a [DEFAULT] section.
        """
        self.sysconfig = ConfigParser()
        self.userconfig = ConfigParser()
        system = platform.system()
        if system == "Linux":
            self.sysconfig_file = '/etc/beeflow/bee.conf'
            self.userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
        elif system == "Darwin":
            self.sysconfig_file = '/Library/Application Support/beeflow/bee.conf'
            self.userconfig_file = os.path.expanduser('~/Library/Application Support/beeflow/bee.conf')
        elif system == "Windows":
            self.sysconfig_file = ''
            self.userconfig_file = os.path.expandvars(r'%APPDATA%\beeflow\bee.conf')

        try:
            with open(self.sysconfig_file) as sysconf_file:
                self.sysconfig.read_file(sysconf_file)
                sysconf_file.close()
        except FileNotFoundError:
            pass

        try:
            with open(self.userconfig_file) as userconf_file:
                self.userconfig.read_file(userconf_file)
                userconf_file.close()
        except FileNotFoundError:
            os.makedirs(os.path.dirname(self.userconfig_file), exist_ok=True)
            with open(self.userconfig_file, 'w') as conf:
                conf.write("# BEE CONFIGURATION FILE #")
                conf.close()
            default_workdir = os.path.expanduser('~/.beeflow')
            default_dict = {
                'name': 'DEFAULT',
                'bee_workdir': str(default_workdir),
                }
            self.add_section('user', default_dict)

    def add_section(self, conf, secdict):
        """Add a new section to the system or user config file.

        :param conf: which config file to edit
        :type conf: string, 'user', 'system', or 'both'
        :param secdict: key-value pairs of configuration variable
        :type secdict: dictionary, first entry MUST BE 'name': <value> of the new section
        """
        section_name = secdict.pop('name')
        newconfig = ConfigParser()
        newconfig[str(section_name)] = secdict
        if conf == 'user':
            with open(self.userconfig_file, 'a')as configfile:
                configfile.write('\n')
                newconfig.write(configfile)
                configfile.close()
