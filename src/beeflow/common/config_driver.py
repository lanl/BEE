"""BEE configuration driver module."""

from configparser import ConfigParser
import os
import sys
import platform
import argparse
import textwrap

from beeflow.common.config_validator import ConfigValidator


_SYSTEM = platform.system()


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

    CONFIG = None
    # Set default config locations
    if _SYSTEM == 'Linux':
        SYSCONFIG_FILE = '/etc/beeflow/bee.conf'
        USERCONFIG_FILE = os.path.expanduser('~/.config/beeflow/bee.conf')
    elif _SYSTEM == 'Darwin':
        SYSCONFIG_FILE = '/Library/Application Support/beeflow/bee.conf'
        USERCONFIG_FILE = os.path.expanduser(
            '~/Library/Application Support/beeflow/bee.conf')
    elif _SYSTEM == 'Windows':
        SYSCONFIG_FILE = None
        USERCONFIG_FILE = os.path.expandvars(r'%APPDATA%\beeflow\bee.conf')

    def __init__(self, **kwargs):
        raise RuntimeError(
            'BeeConfig is a singleton class. Call BeeConfig.init() once to initialize.'
        )

    @classmethod
    def init(cls, userconfig=None, **kwargs):
        """Initialize BeeConfig class.

        We check the platform and read in system and user configuration files.
        If the user configuration file doesn't exist we create it with a [DEFAULT] section.
        """
        if cls.CONFIG is not None:
            raise RuntimeError(
                'BeeConfig.init() has been called more than once. BeeConfig is a singleton class.'
            )
        config = ConfigParser()
        system = platform.system()
        #if system == "Linux":
        #    sysconfig_file = '/etc/beeflow/bee.conf'
        #    try:
        #        # Accept user_config option
        #        userconfig_file = kwargs['userconfig']
        #    except KeyError:
        #        userconfig_file = os.path.expanduser('~/.config/beeflow/bee.conf')
        #elif system == "Darwin":
        #    sysconfig_file = '/Library/Application Support/beeflow/bee.conf'
        #    userconfig_file = os.path.expanduser(
        #        '~/Library/Application Support/beeflow/bee.conf')
        #elif system == "Windows":
        #    sysconfig_file = ''
        #    try:
        #        # Accept user_config option
        #        userconfig_file = kwargs['userconfig']
        #    except KeyError:
        #        userconfig_file = os.path.expandvars(r'%APPDATA%\beeflow\bee.conf')
        #if userconfig is None:
        #    userconfig = userconfig_file
        if userconfig is not None:
            cls.USERCONFIG_FILE = userconfig
        # Try and read the file
        with open(cls.USERCONFIG_FILE) as fp:
            config.read_file(fp)
        # remove default keys from the other sections
        default_keys = [key for key in config['DEFAULT']]
        config = {sec_name: {key: config[sec_name][key] for key in config[sec_name]
                             if sec_name == 'DEFAULT' or key not in default_keys}
                  for sec_name in config}
        # Validate the config
        cls.CONFIG = VALIDATOR.validate(config)

    @classmethod
    def userconfig_path(cls):
        """Get the path of the user config."""
        return cls.USERCONFIG_FILE

    @classmethod
    def get(cls, sec_name, opt_name):
        """Get a configuration value.

           If this throws, then either BeeConfig has not been initialized or a
           configuration value is missing from the definition. Default values
           are built into the ConfigValidator class, so there is no need to
           specify a default here."""
        if cls.CONFIG is None:
            raise RuntimeError('BeeConfig has not been initialized')
        return cls.CONFIG[sec_name][opt_name]

    @staticmethod
    def resolve_path(relative_path):
        """Resolve relative paths to absolute paths.

        :param relative_path: Input path. May include "../"
        :type relative_path: string, path to file
        """
        # Discard redundant paths, iff Windows, replace(\,/)
        # Assume "~" means home dir
        relative_path = os.path.expanduser(os.path.normpath(relative_path))
        # Resolve the true path (expand relative path refs)
        tmp = os.getcwd()
        if os.path.isdir(relative_path):
            os.chdir(relative_path)
            absolute_path = os.getcwd()
        else:
            # Get desired config file name
            filename = os.path.basename(relative_path)
            os.chdir(os.path.dirname(relative_path))
            absolute_path = '/'.join([os.getcwd(), filename])
        os.chdir(tmp)
        return absolute_path


# Specialized validation functions

def validate_dir(path):
    """Check that the path exists and is a directory."""
    if not os.path.exists(path):
        raise ValueError('path "{}" does not exist'.format(path))
    if not os.path.isdir(path):
        raise ValueError('path "{}" is not a directory'.format(path))
    return path


# Below is the definition of all bee config options, defaults and requirements.
# This will be used to validate config files on loading them in the BeeConfig
# singleton class above.
#
# Set up default ports, get parent's pid to offset ports.
# Windows note: uid method better but not available in Windows
if platform.system() == 'Windows':
    # Would prefer something like a uid for windows.
    OFFSET = os.getppid() % 100
else:
    OFFSET = os.getuid() % 100
DEFAULT_BOLT_PORT = 7687 + OFFSET
DEFAULT_HTTP_PORT = 7474 + OFFSET
DEFAULT_HTTPS_PORT = 7473 + OFFSET
DEFAULT_WFM_PORT = 5000 + OFFSET
DEFAULT_TM_PORT = 5050 + OFFSET
DEFAULT_SCHED_PORT = 5100 + OFFSET
# Create the validator
VALIDATOR = ConfigValidator('BEE configuration file and validation information.')
VALIDATOR.section('DEFAULT', info='Default bee.conf configuration section.')
VALIDATOR.option('DEFAULT', 'bee_workdir', required=True, info='main BEE workdir', validator=validate_dir)
VALIDATOR.option('DEFAULT', 'workload_scheduler', required=True, choices=('Slurm', 'LSF', 'Simple'),
                 info='backend workload scheduler to interact with ')
VALIDATOR.option('DEFAULT', 'use_archive', default=False, validator=bool,
                 info='use the BEE archiving functinality')
# Workflow Manager
VALIDATOR.section('workflow_manager', info='Workflow manager section.')
VALIDATOR.option('workflow_manager', 'listen_port', default=DEFAULT_WFM_PORT, validator=int,
                 info='workflow manager port')
# Task manager
VALIDATOR.section('task_manager', info='Task manager configuration and config of container to use.')
VALIDATOR.option('task_manager', 'listen_port', default=DEFAULT_TM_PORT, validator=int,
                 info='task manager listen port')
VALIDATOR.option('task_manager', 'container_runtime', default='Charliecloud',
                 choices=('Charliecloud', 'Singularity'),
                 info='container runtime to use for configuration')
VALIDATOR.option('task_manager', 'job_template', required=True,
                 info='job template to use for generating submission scripts')
# Charliecloud (depends on task_manager::container_runtime == Charliecloud)
HOME_DIR = os.path.expanduser('~/')
VALIDATOR.section('charliecloud', info='Charliecloud configuration section.',
                  depends_on=('task_manager', 'container_runtime', 'Charliecloud'))
VALIDATOR.option('charliecloud', 'image_mntdir', default='/tmp',
                 info='Charliecloud mount directory')
VALIDATOR.option('charliecloud', 'chrun_opts', default=f'--cd {HOME_DIR}',
                 info='extra options to pass to ch-run')
VALIDATOR.option('charliecloud', 'container_dir', required=True,
                 info='Charliecloud container directory')
# Graph Database
VALIDATOR.section('graphdb', info='Main graph database configuration section.')
VALIDATOR.option('graphdb', 'hostname', default='localhost', info='hostname of database')
VALIDATOR.option('graphdb', 'dbpass', default='password', info='password for database')
VALIDATOR.option('graphdb', 'bolt_port', default=DEFAULT_BOLT_PORT, validator=int,
                 info='port used for the BOLT API')
VALIDATOR.option('graphdb', 'http_port', default=DEFAULT_HTTP_PORT, validator=int,
                 info='HTTP port used for the graph database')
VALIDATOR.option('graphdb', 'https_port', default=DEFAULT_HTTPS_PORT,
                 info='HTTPS port used for the graph database')
VALIDATOR.option('graphdb', 'gdb_image', required=True, info='graph database container image file')
VALIDATOR.option('graphdb', 'gdb_image_mntdir', default='/tmp',
                 info='graph database image mount directory')
VALIDATOR.option('graphdb', 'sleep_time', validator=int,
                 info='how long to wait for the graph database to come up (this can take a while, '
                      'depending on the system)')
# Builder
VALIDATOR.section('builder', info='General builder configuration section.')
VALIDATOR.option('builder', 'deployed_image_root', default='/tmp',
                 info='where to deploy container images')
VALIDATOR.option('builder', 'container_output_path', default='/tmp',
                 info='container output path')
VALIDATOR.option('builder', 'container_archive',
                 default=os.path.join(HOME_DIR, 'container_archive'),
                 info='container archive location')
VALIDATOR.option('builder', 'container_type', default='charliecloud', info='container type to use')
# Slurmrestd (depends on DEFAULT:workload_scheduler == Slurm)
VALIDATOR.section('slurmrestd', info='Configuration section for Slurmrestd.',
                  depends_on=('DEFAULT', 'workload_scheduler', 'Slurm'))
VALIDATOR.option('slurmrestd', 'slurm_socket', default='/tmp/slurm.sock', info='socket location')
VALIDATOR.option('slurmrestd', 'slurm_args', default='-s openapi/v0.0.35',
                 info='arguments for the slurmrestd binary')
# Scheduler
VALIDATOR.section('scheduler', info='Scheduler configuration section.')
VALIDATOR.option('scheduler', 'listen_port', default=DEFAULT_SCHED_PORT, validator=int,
                 info='scheduler port')


def print_wrap(text, next_line_indent=''):
    """Print while wrapping lines to make the output easier to read."""
    for line in textwrap.wrap(text, width=80, subsequent_indent=next_line_indent):
        print(line)


def info(validator):
    """Display some info about bee.conf's various options."""
    #out = []
    print('# BEE Configuration')
    print()
    print_wrap(validator.description)
    print()
    for sec_name, section in validator.sections:
        print('## {}'.format(sec_name))
        if section.depends_on is not None:
            print()
            print_wrap('*only required if %s::%s == "%s"*' % section.depends_on)
        print()
        print_wrap('{}'.format(section.info))
        print()
        for opt_name, option in validator.options(sec_name):
            required_text = '*required* ' if option.required else ''
            print_wrap('* {} - {}{}'.format(opt_name, required_text, option.info), '  ')
            if option.choices is not None:
                print('\t* allowed values: {}'.format(option.choices))
        print()


def new_conf(fname, validator):
    """Create a new bee configuration based on user input."""
    print('Creating a new config: "{}".'.format(fname))
    print()
    print_wrap('This will walk you through creating a new configuration for BEE. '
               'Note that you will only be required to enter values for required '
               'options. Please take a look at the other options and their '
               'defaults before running BEE.')
    print()
    print('Please enter values for the following options:')
    sections = {}
    for sec_name, section in validator.sections:
        sections[sec_name] = {}
        printed = False
        for opt_name, option in validator.options(sec_name):
            if not option.required:
                continue
            # Print the section name if it has a required option and it hasn't
            # already been printed.
            if not printed:
                print('[{}]'.format(sec_name))
                printed = True
            value = None
            # input and then validate the value
            while value is None:
                print('#', option.info)
                value = input('{} = '.format(opt_name))
                try:
                    option.validate(value)
                except ValueError as ve:
                    print(ve)
                    value = None
            sections[sec_name][opt_name] = value
    print()
    print('The following configuration options were chosen:')
    for sec_name in sections:
        for opt_name in sections[sec_name]:
            print('{}::{} = {}'.format(sec_name, opt_name, sections[sec_name][opt_name]))
    ans = input('Are these correct? [y/n] ')
    if ans.lower() != 'y':
        print('Quitting without saving')
        return
    with open(fname, 'w') as fp:
        for sec_name in sections:
            if not sections[sec_name]:
                continue
            print('[{}]'.format(sec_name), file=fp)
            for opt_name in sections[sec_name]:
                print('{} = {}'.format(opt_name, sections[sec_name][opt_name]), file=fp)
    print('Saved config to "{}"'.format(fname))
    print()
    print_wrap('Before running BEE, make sure to check that other default options are compatible with your system.')


def main():
    """Entry point for config validation and help."""
    parser = argparse.ArgumentParser(description='BEE configuration helper and validator')
    parser.add_argument('--validate', '-v', validator=str,
                        help='validate a configuration file')
    parser.add_argument('--info', '-i', action='store_true',
                        help='print general info for each configuration')
    parser.add_argument('--new', '-n', validator=str, default=None,
                        help='create a new bee conf file')
    args = parser.parse_args()
    # Load and validate the bee.conf
    if args.validate:
        # BeeConfig auto validates the file on load
        BeeConfig.init(args.validate)
    if args.info:
        info(VALIDATOR)
    if args.new is not None:
        new_conf(args.new, VALIDATOR)


if __name__ == '__main__':
    main()
