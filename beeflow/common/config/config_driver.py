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

    def __init__(self, **kwargs):
        """Initialize BeeConfig class.

        We check the platform and read in system and user configuration files.
        If the user configuration file doesn't exist we create it with a [DEFAULT] section.
        """
        self.sysconfig = ConfigParser()
        self.userconfig = ConfigParser()
        system = platform.system()
        if system == "Linux":
            self.sysconfig_file = '/etc/beeflow/bee.conf'
            try:
                # Accept user_config option
                self.userconfig_file = kwargs['userconfig']
            except KeyError: 
                self.userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
        elif system == "Darwin":
            self.sysconfig_file = '/Library/Application Support/beeflow/bee.conf'
            try:
                # Accept user_config option
                self.userconfig_file = kwargs['userconfig']
            except KeyError: 
                self.userconfig_file = os.path.expanduser('~/Library/Application Support/beeflow/bee.conf')
        elif system == "Windows":
            self.sysconfig_file = ''
            try:
                # Accept user_config option
                self.userconfig_file = kwargs['userconfig']
            except KeyError: 
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
            # Get absolute path
            self.userconfig_file = self.resolve_path(self.userconfig_file)
        except FileNotFoundError:
            # Create directory based on relative path
            os.makedirs(os.path.dirname(self.userconfig_file), exist_ok=True)
            self.userconfig_file = self.resolve_path(self.userconfig_file)
            default_workdir = os.path.dirname(self.userconfig_file)
            default_dict = {
                'name': 'DEFAULT',
                'bee_workdir': str(default_workdir),
                }
            try:
                graphdb_dict = kwargs['graphdb_dict']
            except KeyError:
                if platform.system() == 'Windows':
                    # Need something like a uid for windows.
                    offset = 0
                else:
                    offset = os.getuid()%100         
                graphdb_dict = {
                    'name': 'graphdb',
                    'hostname': 'localhost',
                    'dbpass': 'password',
                    'bolt_port': 7687+offset,
                    'http_port': 7474+offset,
                    'https_port': 7473+offset,
                    'gdb_image': '/usr/projects/beedev/neo4j-3-5-17.tar.gz',
                    'gdb_image_mntdir': default_workdir,
                }
            with open(self.userconfig_file, 'w') as conf_fh:
                conf_fh.write("# BEE CONFIGURATION FILE #")
                conf_fh.close()
            self.add_section('user','DEFAULT',{'bee_workdir':str(default_workdir)})
            self.add_section('user','graphdb',graphdb_dict)

    def add_section(self, conf, section, keyvalue):
            """Add a new section to the system or user config file.
            :param conf: which config file to edit
            :type conf: string, 'user', 'system', or 'both'
            :param section: configuration file section
            :type section: string
            :param keyvalue: configuration variable
            :type key: dict
            """
            if conf == 'user':
                conf_files = [self.userconfig_file]
                conf_objs  = [self.userconfig]
            elif conf == 'system':
                conf_files = [self.sysconfig_file]
                conf_objs  = [self.sysconfig]
            elif conf == 'both':
                conf_files = [self.userconfig_file,
                              self.sysconfig_file]
                conf_objs  = [self.userconfig,
                              self.sysconfig]
            else:
                raise NotImplementedError('Only user, system, or both are config \
                                           file options')
            for conf_file,conf_obj in zip(conf_files,conf_objs):
                # Update conf_obj with current file as written
                with open(conf_file, 'r')as conf_fh:
                    # Object reads filehandle
                    conf_obj.read_file(conf_fh)
                    conf_fh.close()
                # Insert new value
                try:
                    conf_obj[section]
                except KeyError:
                    conf_obj[section] = {}
                finally:
                    # Update if values already present
                    try:
                        conf_obj[section].update(keyvalue)
                    # Set if value not present
                    except TypeError:
                        conf_obj[section] = keyvalue
                # Write altered conf_obj back to file
                with open(conf_file, 'w')as conf_fh:
                    conf_fh.write("# BEE CONFIGURATION FILE #\n")
                    # Object writes to filehandle
                    conf_obj.write(conf_fh)
                    conf_fh.close()

    def resolve_path(self, relative_path):
        """Resolve relative paths to absolute paths
 
        :param relative_path: Input path. May include "../"
        :type relative_path: string, path to file
        """
        # Discard redundant paths, iff Windows, replace(\,/)
        relative_path = os.path.normpath(relative_path)
        # Get desired config file name
        filename = os.path.basename(relative_path)
        # Resolve the true path (expand relative path refs)
        tmp = os.getcwd()
        os.chdir(os.path.dirname(relative_path))
        absolute_path = '/'.join([os.getcwd(),filename])
        os.chdir(tmp)
        return(absolute_path)
