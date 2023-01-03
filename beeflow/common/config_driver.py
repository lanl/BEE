"""BEE configuration driver module."""

from configparser import ConfigParser
import getpass
import os
import platform
import random
import shutil
import sys
import textwrap
import typer

from beeflow.common.config_validator import ConfigValidator
from beeflow.common.cli import NaturalOrderGroup


# System specific path set up
HOME_DIR = os.path.expanduser('~/')
_SYSTEM = platform.system()
if _SYSTEM == 'Linux':
    CONF_DIR = os.path.join(HOME_DIR, '.config/beeflow')
    SYSCONFIG_FILE = '/etc/beeflow/bee.conf'
    USERCONFIG_FILE = os.path.expanduser('~/.config/beeflow/bee.conf')
elif _SYSTEM == 'Darwin':
    CONF_DIR = os.path.expanduser('~/Library/Application Support/beeflow')
    SYSCONFIG_FILE = '/Library/Application Support/beeflow/bee.conf'
    USERCONFIG_FILE = os.path.expanduser(
        '~/Library/Application Support/beeflow/bee.conf')
elif _SYSTEM == 'Windows':
    CONF_DIR = os.path.expandvars(r'%APPDATA%\beeflow')
    SYSCONFIG_FILE = None
    USERCONFIG_FILE = os.path.expandvars(r'%APPDATA%\beeflow\bee.conf')
else:
    raise RuntimeError(f'System "{_SYSTEM}" is not supported')


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

      userconfig_file = '%APPDATA%\\beeflow\\bee.conf'
    """

    CONFIG = None

    def __init__(self, **kwargs):
        """Do not use this constructor."""
        raise RuntimeError(
            'BeeConfig is a singleton class. Call BeeConfig.init() once to initialize.'
        )

    @classmethod
    def ready(cls):
        """Check if the class has been initialized."""
        return cls.CONFIG is not None

    @classmethod
    def init(cls, userconfig=None, **_kwargs):
        """Initialize BeeConfig class.

        We check the platform and read in system and user configuration files.
        If the user configuration file doesn't exist we create it with a [DEFAULT] section.
        """
        global USERCONFIG_FILE
        if cls.CONFIG is not None:
            return
        config = ConfigParser()
        if userconfig is not None:
            USERCONFIG_FILE = userconfig
        # Try and read the file
        try:
            with open(USERCONFIG_FILE, encoding='utf-8') as fp:
                config.read_file(fp)
        except FileNotFoundError:
            sys.exit('Configuration file does not exist! Please try running `beecfg new`.')
        # remove default keys from the other sections
        default_keys = list(config['DEFAULT'])
        config = {sec_name: {key: config[sec_name][key] for key in config[sec_name]
                             if sec_name == 'DEFAULT' or key not in default_keys} # noqa
                  for sec_name in config}
        # Validate the config
        cls.CONFIG = VALIDATOR.validate(config)

    @classmethod
    def userconfig_path(cls):
        """Get the path of the user config."""
        return USERCONFIG_FILE

    @classmethod
    def get(cls, sec_name, opt_name):
        """Get a configuration value.

        If this throws, then either BeeConfig has not been initialized or a
        configuration value is missing from the definition. Default values
        are built into the ConfigValidator class, so there is no need to
        specify a default or a fallback here.
        """
        if cls.CONFIG is None:
            raise RuntimeError('BeeConfig has not been initialized')
        try:
            return cls.CONFIG[sec_name][opt_name] # noqa (this object is subscritable)
        except KeyError:
            raise RuntimeError(
                f'Option {sec_name}::{opt_name} was not found. Please contact '
                'a BEE developer or check the validation code in '
                'beeflow/common/config_driver.py.'
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


def validate_make_dir(path):
    """Check if the dir exists and if not create it."""
    os.makedirs(path, exist_ok=True)
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


def validate_bool(value):
    """Validate a boolean value."""
    return str(value).lower() == 'true'


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


def job_template_init(path, cur_opts):
    """Job template init function.

    :param path: chosen path of Jinja job template file
    :param cur_opts: current chosen options from the config generator
    :return: initialized Jinja template path
    """
    path = os.path.expanduser(path)
    if os.path.exists(path):
        return path
    print('Check that options (like accounts)for your particular system are satisfied.')
    if not check_yes(f'Do you want to write a default job template to:\n "{path}"?'):
        return path
    # Check for workload_scheduler in cur_opts (NB: this will need to be updated
    # if the option name changes later on)
    if 'DEFAULT' in cur_opts and 'workload_scheduler' in cur_opts['DEFAULT']:
        template = cur_opts['DEFAULT']['workload_scheduler']
    else:
        template = check_choice('What template should be generated?', ('Slurm', 'LSF', 'Simple'))
    template_files = {
        'Slurm': 'slurm-submit.jinja',
        'LSF': 'lsf-submit.jinja',
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
    return path


def bee_workdir_init(path, _cur_opts):
    """BEE workdir init function.

    :param path: chosen path for the bee workdir
    :param _cur_opts: current chosen options form the config generator
    :return: initialized bee workdir path
    """
    path = os.path.expanduser(path)
    if os.path.exists(path):
        return path
    if not check_yes(f'Path "{path}" does not exist.\nWould you like to create it?'):
        return path
    os.makedirs(path)
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

SOCKET_PATH = join_path(HOME_DIR, '.beeflow', 'sockets')
os.makedirs(SOCKET_PATH, exist_ok=True)
DEFAULT_WFM_SOCKET = join_path(SOCKET_PATH, 'wf_manager.sock')
DEFAULT_TM_SOCKET = join_path(SOCKET_PATH, 'task_manager.sock')
DEFAULT_SCHED_SOCKET = join_path(SOCKET_PATH, 'scheduler.sock')
DEFAULT_BEEFLOW_SOCKET = join_path(SOCKET_PATH, 'beeflow.sock')

DEFAULT_BEE_WORKDIR = join_path(HOME_DIR, '.beeflow')
USER = getpass.getuser()
# Create the validator
VALIDATOR = ConfigValidator('BEE configuration file and validation information.')
VALIDATOR.section('DEFAULT', info='Default bee.conf configuration section.')
VALIDATOR.option('DEFAULT', 'bee_workdir', info='main BEE workdir',
                 attrs={'default': DEFAULT_BEE_WORKDIR}, validator=validate_make_dir)
VALIDATOR.option('DEFAULT', 'workload_scheduler', choices=('Slurm', 'LSF', 'Simple'),
                 info='backend workload scheduler to interact with ')
VALIDATOR.option('DEFAULT', 'use_archive', validator=validate_bool, attrs={'default': True},
                 info='use the BEE archiving functinality')
VALIDATOR.option('DEFAULT', 'bee_dep_image', validator=validate_file,
                 info='container image with BEE dependencies')
VALIDATOR.option('DEFAULT', 'beeflow_pidfile',
                 attrs={'default': join_path(DEFAULT_BEE_WORKDIR, 'beeflow.pid')},
                 info='location of beeflow pidfile')
VALIDATOR.option('DEFAULT', 'beeflow_socket',
                 attrs={'default': DEFAULT_BEEFLOW_SOCKET},
                 info='location of beeflow socket')
# Workflow Manager
VALIDATOR.section('workflow_manager', info='Workflow manager section.')
VALIDATOR.option('workflow_manager', 'socket',
                 attrs={'default': DEFAULT_WFM_SOCKET}, validator=str,
                 info='workflow manager port')
# Task manager
VALIDATOR.section('task_manager',
                  info='Task manager configuration and config of container to use.')
VALIDATOR.option('task_manager', 'socket', attrs={'default': DEFAULT_TM_SOCKET}, validator=str,
                 info='task manager listen port')
VALIDATOR.option('task_manager', 'container_runtime', attrs={'default': 'Charliecloud'},
                 choices=('Charliecloud', 'Singularity'),
                 info='container runtime to use for configuration')
VALIDATOR.option('task_manager', 'runner_opts', validator=str, attrs={'default': ''},
                 info='special runner options to pass to the runner opts')
# Note: I've added a special attrs keyword which can include anything. In this
# case it's being used to store a special 'init' function that can be used to
# initialize the parameter when a user is generating a new configuration.
VALIDATOR.option('task_manager', 'job_template',
                 info='job template to use for generating submission scripts',
                 validator=validate_file,
                 attrs={'init': job_template_init, 'default': join_path(CONF_DIR, 'submit.jinja')})
# Charliecloud (depends on task_manager::container_runtime == Charliecloud)
VALIDATOR.section('charliecloud', info='Charliecloud configuration section.',
                  depends_on=('task_manager', 'container_runtime', 'Charliecloud'))
VALIDATOR.option('charliecloud', 'image_mntdir', attrs={'default': join_path('/tmp', USER)},
                 info='Charliecloud mount directory', validator=validate_make_dir)


def validate_chrun_opts(opts):
    """Ensure that chrun_opts don't contain options that'll conflict with BEE."""
    args = opts.split()
    if '--cd' in args or '-c' in args:
        raise ValueError('Initial working directory option (-c or --cd) conflicts with BEE. '
                         'Please make sure that you choose the correct working directory on '
                         'workflow submission.')
    return opts


VALIDATOR.option('charliecloud', 'chrun_opts', attrs={'default': ''},
                 validator=validate_chrun_opts,
                 info='extra options to pass to ch-run')
VALIDATOR.option('charliecloud', 'setup', attrs={'default': ''}, validator=str,
                 info='extra Charliecloud setup to put in a job script')
# Graph Database
VALIDATOR.section('graphdb', info='Main graph database configuration section.')
VALIDATOR.option('graphdb', 'hostname', attrs={'default': 'localhost'},
                 info='hostname of database')
VALIDATOR.option('graphdb', 'dbpass', attrs={'default': 'password'}, info='password for database')
VALIDATOR.option('graphdb', 'bolt_port', attrs={'default': DEFAULT_BOLT_PORT}, validator=int,
                 info='port used for the BOLT API')
VALIDATOR.option('graphdb', 'http_port', attrs={'default': DEFAULT_HTTP_PORT}, validator=int,
                 info='HTTP port used for the graph database')
VALIDATOR.option('graphdb', 'https_port', attrs={'default': DEFAULT_HTTPS_PORT},
                 info='HTTPS port used for the graph database')
VALIDATOR.option('graphdb', 'gdb_image_mntdir', attrs={'default': join_path('/tmp', USER)},
                 info='graph database image mount directory', validator=validate_make_dir)
VALIDATOR.option('graphdb', 'sleep_time', validator=int, attrs={'default': 10},
                 info='how long to wait for the graph database to come up (this can take a while, '
                      'depending on the system)')
# Builder
VALIDATOR.section('builder', info='General builder configuration section.')
VALIDATOR.option('builder', 'deployed_image_root', attrs={'default': '/tmp'},
                 info='where to deploy container images', validator=validate_make_dir)
VALIDATOR.option('builder', 'container_output_path', attrs={'default': '/tmp'},
                 info='container output path', validator=validate_make_dir)
VALIDATOR.option('builder', 'container_archive',
                 attrs={'default': join_path(DEFAULT_BEE_WORKDIR, 'container_archive')},
                 info='container archive location')
VALIDATOR.option('builder', 'container_type', attrs={'default': 'charliecloud'},
                 info='container type to use')
# Slurmrestd (depends on DEFAULT:workload_scheduler == Slurm)
VALIDATOR.section('slurmrestd', info='Configuration section for Slurmrestd.',
                  depends_on=('DEFAULT', 'workload_scheduler', 'Slurm'))
DEFAULT_SLURMRESTD_SOCK = join_path('/tmp', f'slurm_{USER}_{random.randint(1, 10000)}.sock')
VALIDATOR.option('slurmrestd', 'slurm_socket', attrs={'default': DEFAULT_SLURMRESTD_SOCK},
                 info='socket location')
VALIDATOR.option('slurmrestd', 'slurm_args', attrs={'default': '-s openapi/v0.0.35'},
                 info='arguments for the slurmrestd binary')
# Scheduler
VALIDATOR.section('scheduler', info='Scheduler configuration section.')
VALIDATOR.option('scheduler', 'log',
                 attrs={'default': join_path(DEFAULT_BEE_WORKDIR, 'logs', 'scheduler.log')},
                 validator=str, info='scheduler log file')
VALIDATOR.option('scheduler', 'socket', attrs={'default': DEFAULT_SCHED_SOCKET}, validator=str,
                 info='scheduler socket')
VALIDATOR.option('scheduler', 'alloc_logfile',
                 attrs={'default': join_path(DEFAULT_BEE_WORKDIR, 'logs', 'scheduler_alloc.log')},
                 validator=str, info='allocation logfile, to be used for later training')
SCHEDULER_ALGORITHMS = ('fcfs', 'backfill', 'sjf')
VALIDATOR.option('scheduler', 'algorithm', attrs={'default': 'fcfs'}, choices=SCHEDULER_ALGORITHMS,
                 info='scheduling algorithm to use')
VALIDATOR.option('scheduler', 'default_algorithm', attrs={'default': 'fcfs'},
                 choices=SCHEDULER_ALGORITHMS,
                 info=('default algorithm to use'))
VALIDATOR.option('scheduler', 'workdir',
                 attrs={'default': join_path(DEFAULT_BEE_WORKDIR, 'scheduler')},
                 validator=str,
                 info='workdir to be used for the scheduler')


def print_wrap(text, next_line_indent=''):
    """Print while wrapping lines to make the output easier to read."""
    for line in textwrap.wrap(text, width=80, subsequent_indent=next_line_indent):
        print(line)


class ConfigGenerator:
    """Config generator class."""

    def __init__(self, fname, validator):
        """Construct the config generator."""
        self.fname = fname
        self.validator = validator
        self.sections = {}

    def choose_values(self):
        """Choose configuration values based on user input."""
        dirname = os.path.dirname(self.fname)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        print(f'Creating a new config: "{self.fname}".')
        print()
        print_wrap('This will walk you through creating a new configuration for BEE. '
                   'Note that you will only be required to enter values for options '
                   'without defaults. Please take a look at the other options and '
                   'their defaults before running BEE.')
        print()
        print('Please enter values for the following sections and options:')
        # Let the user choose values for each required attribute
        for sec_name, section in self.validator.sections:
            # Determine if this section is valid under the current configuration
            if not self.validator.is_section_valid(self.sections, sec_name):
                continue
            self.sections[sec_name] = {}
            printed = False
            for opt_name, option in self.validator.options(sec_name):
                # Print the section name if it hasn't already been printed.
                if not printed:
                    print()
                    print(f'## {sec_name}')
                    print()
                    print_wrap(section.info)
                    print()
                    printed = True
                if option.attrs is not None and 'default' in option.attrs:
                    default = option.attrs['default']
                    if option.attrs is not None and 'init' in option.attrs:
                        value = option.attrs['init'](default, self.sections)
                    else:
                        value = option.validate(default)
                    print(f'Setting option "{opt_name}" to default value "{value}".')
                    print()
                    self.sections[sec_name][opt_name] = value
                    continue
                value = None
                # Input and then validate the value
                while value is None:
                    print_wrap(f'{opt_name} - {option.info}')
                    if option.choices is not None:
                        print(f'(allowed values: {",".join(option.choices)})')
                    value = input(f'{opt_name}: ')
                    # Call the init function if there is one
                    if option.attrs is not None and 'init' in option.attrs:
                        option.attrs['init'](value, self.sections)
                    try:
                        option.validate(value)
                    except ValueError as err:
                        print('ERROR:', err)
                        value = None
                print()
                self.sections[sec_name][opt_name] = value
        return self

    def save(self):
        """Save the config to a file."""
        print()
        print('The following configuration options were chosen:')
        for sec_name, section in self.sections.items():
            print()
            print(f'[{sec_name}]')
            for opt_name in section:
                print(f'{opt_name} = {section[opt_name]}')
        print()
        ans = input('Would you like to save this config? [y/n] ')
        if ans.lower() != 'y':
            print('Quitting without saving')
            return
        try:
            with open(self.fname, 'w', encoding='utf-8') as fp:
                print('# BEE Configuration File', file=fp)
                for sec_name, section in self.sections.items():
                    if not section:
                        continue
                    print(file=fp)
                    print(f'[{sec_name}]'.format(sec_name), file=fp)
                    for opt_name in section:
                        print(f'{opt_name} = {section[opt_name]}', file=fp)
        except FileNotFoundError:
            print('Configuration file does not exist!')
        print(70 * '#')
        print('Before running BEE, check defaults in the configuration file:',
              f'\n\t{self.fname}',
              '\n ** See documentation for values you should refrain from editing! **',
              '\n\nThe job template configured is:',
              f'\n\t{self.sections["task_manager"]["job_template"]}',
              '\n ** Include job options (such as account) required for this system.**')
        print('\n(Try `beecfg info` to see more about each option)')
        print(70 * '#')


app = typer.Typer(no_args_is_help=False, add_completion=False, cls=NaturalOrderGroup)


@app.command()
def validate(path: str = typer.Argument(default=USERCONFIG_FILE,
                                        help='Path to config file')):
    """Validate an existing configuration file."""
    BeeConfig.init(path)


@app.command()
def info():
    """Display some info about bee.conf's various options."""
    print('# BEE Configuration')
    print()
    print_wrap(VALIDATOR.description)
    print()
    for sec_name, section in VALIDATOR.sections:
        print(f'## {sec_name}')
        if section.depends_on is not None:
            print()
            deps = section.depends_on
            print_wrap(f'*only required if {deps[0]}::{deps[1]} == "{deps[2]}"*')
        print()
        print_wrap(f'{section.info}')
        print()
        for opt_name, option in VALIDATOR.options(sec_name):
            print_wrap(f'* {opt_name} - {option.info}', '  ')
            if option.choices is not None:
                print(f'\t* allowed values: {",".join(option.choices)}')
        print()


@app.command()
def new(path: str = typer.Argument(default=USERCONFIG_FILE,
                                   help='Path to new config file')):
    """Create a new config file."""
    if os.path.exists(path):
        if check_yes(f'Path "{path}" already exists.\nWould you like to save a copy of it?'):
            i = 1
            backup_path = f'{path}.{i}'
            while os.path.exists(backup_path):
                i += 1
                backup_path = f'{path}.{i}'
            shutil.copy(path, backup_path)
            print(f'Saved old config to "{backup_path}".')
            print()
    ConfigGenerator(path, VALIDATOR).choose_values().save()


@app.command()
def show(path: str = typer.Argument(default=USERCONFIG_FILE,
                                    help='Path to config file')):
    """Show the contents of bee.conf."""
    if not os.path.exists(path):
        print('The bee.conf does not exist yet. Please run `beecfg new`.')
        return
    print(f'# {path}')
    with open(path, encoding='utf-8') as fp:
        print(fp.read(), end='')


def main():
    """Entry point for config validation and help."""
    app()


if __name__ == '__main__':
    app()
