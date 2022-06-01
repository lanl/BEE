"""BEE configuration driver module."""

from configparser import ConfigParser
import os
import sys
import pkgutil
import platform
import argparse
import shutil
import textwrap

from beeflow.common.config_validator import ConfigValidator


_SYSTEM = platform.system()


class BeeConfig:
    r"""Class to manage and store all BEE configuration.

    All configuration values can be retrieved by using the get(section, key)
    class method. If those particular values are not in the config file, then
    defaults will be set, or a validation error raised, based on the validation code
    within the module.

    When new configuration keys are needed, they should be added to the
    validation code, along with information about the allowed input types, and
    general text for the user. If a key isn't added, but other code tries to
    access it, then an error will be raised letting the programmer know that the
    key needs to be added to the validation. This will hopefully help manage
    complexity and act as documentation as more keys are added.

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
    def ready(cls):
        """Check if the class is ready (i.e. if BeeConfig has been initialized)."""
        return cls.CONFIG is not None

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
        try:
            return cls.CONFIG[sec_name][opt_name]
        except KeyError:
            raise RuntimeError(
                f'Option {sec_name}::{opt_name} was not found. Please contact '
                'a BEE developer or check the validation code in '
                'src/beeflow/common/config_driver.py.'
            ) from None

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


def check_yes(msg):
    """Check for a y/n answer."""
    res = input(f'{msg} [y/n] ')
    return res.lower() == 'y'

# Specialized functions for validation and config initialization

def validate_path(path):
    """Check that the path exists."""
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        raise ValueError(f'path "{path}" does not exist')
    return path


def validate_dir(path):
    """Check that the path exists and is a directory."""
    path = validate_path(path)
    if not os.path.isdir(path):
        raise ValueError('path "{path}" is not a directory')
    return path


def validate_file(path):
    """Check that the path exists and is a file."""
    path = validate_path(path)
    if not os.path.isfile(path):
        raise ValueError(f'path "{path}" is not a file')
    return path


def validate_nonnegative_int(value):
    """Validate that the input is nonnegative."""
    i = int(value)
    if i < 0:
        raise ValueError('the value must be nonnegative')
    return i


def check_choice(msg, opts):
    """Ask the user to pick from opts."""
    while True:
        value = input(f'{msg} ({",".join(opts)})')
        if value in opts:
            return value
        print(f'ERROR: invalid option: {value}')


def join_path(*pargs):
    """Join multiple dirnames together to form a path."""
    path = pargs[0]
    for part in pargs[1:]:
        path = os.path.join(path, part)
    return path


def job_template_init(path):
    """Job template init function."""
    if not check_yes(f'Do you want to write a default job template to "{path}"?'):
        return
    template = check_choice('What template should be generated?', ('Slurm', 'LSF', 'Simple'))
    template_files = {
        'Slurm': 'slurm-submit.jinja',
    }
    if template not in template_files:
        raise NotImplementedError(f'generation of template file "{template}" is not implemented')
    fname = template_files[template]
    # I don't like how this is done, but there seems to be some difficulties
    # with using the pkgutil.get_data() method and the importlib.resources
    # module.
    common = os.path.dirname(__file__)
    beeflow = os.path.dirname(common)
    file_path = join_path(beeflow, 'data', 'job_templates', fname)
    shutil.copy(file_path, path)


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
VALIDATOR.option('task_manager', 'runner_opts', validator=str,
                 info='special runner options to pass to the runner opts')
# Note: I've added a special attrs keyword which can include anything. In this
# case it's being used to store a special 'init' function that can be used to
# initialize the parameter when a user is generating a new configuration.
VALIDATOR.option('task_manager', 'job_template', required=True,
                 info='job template to use for generating submission scripts',
                 validator=validate_file,
                 attrs={'init': job_template_init})
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
VALIDATOR.option('scheduler', 'log',
                 default=lambda inst: join_path(inst.get('DEFAULT', 'bee_workdir'), 'logs', 'scheduler.log'),
                 validator=str,
                 info='scheduler log file')
VALIDATOR.option('scheduler', 'listen_port', default=DEFAULT_SCHED_PORT, validator=int,
                 info='scheduler port')
VALIDATOR.option('scheduler', 'use_mars', default=False, validator=bool,
                 info='whether or not to use the MARS scheduler')
VALIDATOR.option('scheduler', 'mars_model', default=None, validator=str,
                 info='location of MARS model')
VALIDATOR.option('scheduler', 'mars_task_cnt', default=3, validator=validate_nonnegative_int,
                 info='minimum number of tasks to cause the MARS scheduler to be invoked')
VALIDATOR.option('scheduler', 'alloc_logfile',
                 default=lambda inst: join_path(inst.get('DEFAULT', 'bee_workdir'), 'logs', 'scheduler_alloc.log'),
                 validator=str,
                 info='allocation logfile, to be used for later training')
VALIDATOR.option('scheduler', 'algorithm', default='FCFS', validator=str,
                 info='scheduling algorithm to use')
VALIDATOR.option('scheduler', 'default_algorithm', default='FCFS', validator=str,
                 info='default algorithm to use, when both MARS and this baseline algorithm are to be used')
VALIDATOR.option('scheduler', 'workdir',
                 default=lambda inst: os.path.join(inst.get('DEFAULT', 'bee_workdir'), 'scheduler'),
                 validator=str,
                 info='workdir to be used for the scheduler')


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
        print(f'## {sec_name}')
        if section.depends_on is not None:
            print()
            print_wrap('*only required if %s::%s == "%s"*' % section.depends_on)
        print()
        print_wrap(f'{section.info}')
        print()
        for opt_name, option in validator.options(sec_name):
            required_text = '*required* ' if option.required else ''
            print_wrap(f'* {opt_name} - {required_text}{option.info}', '  ')
            if option.choices is not None:
                print(f'\t* allowed values: {",".join(option.choices)}')
        print()


class ConfigGenerator:
    """Config generator class."""

    def __init__(self, fname, validator):
        self.fname = fname
        self.validator = validator
        self.sections = {}

    def choose_values(self):
        """Choose configuration values based on user input."""
        print(f'Creating a new config: "{self.fname}".')
        print()
        print_wrap('This will walk you through creating a new configuration for BEE. '
                   'Note that you will only be required to enter values for required '
                   'options. Please take a look at the other options and their '
                   'defaults before running BEE.')
        print()
        print('Please enter values for the following options:')
        # Let the user choose values for each required attribute
        for sec_name, section in self.validator.sections:
            self.sections[sec_name] = {}
            printed = False
            for opt_name, option in self.validator.options(sec_name):
                if not option.required:
                    continue
                init_fn = None
                # Check for an init function
                if option.attrs is not None and 'init' in option.attrs:
                    init_fn = option.attrs['init']
                # Print the section name if it has a required option and it hasn't
                # already been printed.
                if not printed:
                    print('[{}]'.format(sec_name))
                    printed = True
                value = None
                # Input and then validate the value
                while value is None:
                    print('#', option.info)
                    value = input(f'{opt_name} = ')
                    # Call the init function if there is one
                    if init_fn is not None:
                        init_fn(value)
                    try:
                        option.validate(value)
                    except ValueError as ve:
                        print('ERROR:', ve)
                        value = None
                self.sections[sec_name][opt_name] = value
        return self

    def save(self):
        """Save the config to a file."""
        print()
        print('The following configuration options were chosen:')
        for sec_name in self.sections:
            for opt_name in self.sections[sec_name]:
                print('{}::{} = {}'.format(sec_name, opt_name, self.sections[sec_name][opt_name]))
        ans = input('Are these correct? [y/n] ')
        if ans.lower() != 'y':
            print('Quitting without saving')
            return
        with open(self.fname, 'w') as fp:
            for sec_name in self.sections:
                if not self.sections[sec_name]:
                    continue
                print('[{}]'.format(sec_name), file=fp)
                for opt_name in self.sections[sec_name]:
                    print(f'{opt_name} = {self.sections[sec_name][opt_name]}', file=fp)
        print(f'Saved config to "{self.fname}"')
        print()
        print_wrap('Before running BEE, make sure to check that other default options are compatible with your system.')


def main():
    """Entry point for config validation and help."""
    parser = argparse.ArgumentParser(description='BEE configuration helper and validator')
    parser.add_argument('--validate', '-v', type=str,
                        help='validate a configuration file')
    parser.add_argument('--info', '-i', action='store_true',
                        help='print general info for each configuration')
    parser.add_argument('--new', '-n', type=str, default=None,
                        help='create a new bee conf file')
    args = parser.parse_args()
    # Load and validate the bee.conf
    if args.validate:
        # BeeConfig auto validates the file on load
        BeeConfig.init(args.validate)
    if args.info:
        info(VALIDATOR)
    if args.new is not None:
        ConfigGenerator(args.new, VALIDATOR).choose_values().save()


if __name__ == '__main__':
    main()
