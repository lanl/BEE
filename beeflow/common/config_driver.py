"""BEE configuration driver module."""

from configparser import ConfigParser
import getpass
import os
import platform
import random
import shutil
import textwrap
import typer

from beeflow.common.config_validator import ConfigValidator
from beeflow.common import config_utils
from beeflow.common.cli import NaturalOrderGroup
from beeflow.common import validation
from beeflow.common.tab_completion import filepath_completion


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

BEE_CONFIG = os.getenv('BEE_CONFIG')
if BEE_CONFIG is not None:
    USERCONFIG_FILE = BEE_CONFIG


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
    def init(cls, userconfig=None, **_kwargs):
        """Initialize BeeConfig class.

        We check the platform and read in system and user configuration files.
        Note that this only needs to be called if one needs to initialize the
        config from a different file or with different keyword arguments. If
        so, then this must be called before any calls to bc.get() are made,
        since that call will initialize the config with default settings.
        """
        global USERCONFIG_FILE
        if cls.CONFIG is not None:
            return
        config = ConfigParser()
        if userconfig is not None:
            USERCONFIG_FILE = userconfig
        # Try and read the file
        while True:
            try:
                with open(USERCONFIG_FILE, encoding='utf-8') as fp:
                    config.read_file(fp)
                break
            except FileNotFoundError:
                print("Configuration file is missing! Generating new config file.")
                new(USERCONFIG_FILE, interactive=False)
        # remove default keys from the other sections
        cls.CONFIG = config_utils.filter_and_validate(config, VALIDATOR)

    @classmethod
    def userconfig_path(cls):
        """Get the path of the user config."""
        return USERCONFIG_FILE

    @classmethod
    def get(cls, sec_name, opt_name):
        """Get a configuration value.

        If this throws, then the configuration value is missing from the
        definition. Initialize the config if not already initialized. Default
        values are built into the ConfigValidator class, so there is no need
        to specify a default or a fallback here.
        """
        if cls.CONFIG is None:
            cls.init()
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


def filepath_completion_input(*pargs, **kwargs):
    """Input files/paths with tab completion."""
    with filepath_completion():
        return input(*pargs, **kwargs)


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
DEFAULT_WFM_PORT = 5000 + OFFSET
DEFAULT_TM_PORT = 5050 + OFFSET
DEFAULT_SCHED_PORT = 5100 + OFFSET

DEFAULT_NEO4J_IMAGE = join_path('/usr/projects/BEE/neo4j.tar.gz')
DEFAULT_REDIS_IMAGE = join_path('/usr/projects/BEE/redis.tar.gz')

DEFAULT_BEE_WORKDIR = join_path(HOME_DIR, '.beeflow')
DEFAULT_BEE_ARCHIVE_DIR = join_path(DEFAULT_BEE_WORKDIR, 'archives')
DEFAULT_BEE_DROPPOINT = join_path(HOME_DIR, '.beeflow/droppoint')
USER = getpass.getuser()

# Check for default containers; setting to None value results in querying user for path
if os.path.isfile(DEFAULT_NEO4J_IMAGE):
    NEO4J_IMAGE = DEFAULT_NEO4J_IMAGE
else:
    NEO4J_IMAGE = None
if os.path.isfile(DEFAULT_REDIS_IMAGE):
    REDIS_IMAGE = DEFAULT_REDIS_IMAGE
else:
    REDIS_IMAGE = None

# Create the validator
VALIDATOR = ConfigValidator('BEE configuration file and validation information.')
VALIDATOR.section('DEFAULT', info='Default bee.conf configuration section.')

VALIDATOR.option('DEFAULT', 'bee_workdir', info='main BEE workdir',
                 default=DEFAULT_BEE_WORKDIR, validator=validation.make_dir,
                 prompt=True)

VALIDATOR.option('DEFAULT', 'bee_archive_dir', info='directory to store workflow archives',
                 default=DEFAULT_BEE_ARCHIVE_DIR, validator=validation.make_dir,
                 prompt=True)

VALIDATOR.option('DEFAULT', 'bee_droppoint', info='BEE remote workflow drop point',
                 default=DEFAULT_BEE_DROPPOINT, validator=validation.make_dir,
                 prompt=False)

VALIDATOR.option('DEFAULT', 'remote_api', info='BEE remote REST API activation',
                 default=False, validator=validation.bool_, prompt=False)

VALIDATOR.option('DEFAULT', 'remote_api_port', info='BEE remote REST API port',
                 default=7777, validator=int, prompt=False)

VALIDATOR.option('DEFAULT', 'workload_scheduler', choices=('Slurm', 'LSF', 'Flux', 'Simple'),
                 default='Slurm', info='backend workload scheduler to interact with ',
                 prompt=True)

VALIDATOR.option('DEFAULT', 'delete_completed_workflow_dirs', validator=validation.bool_,
                 default=True, info='delete workflow directory for completed jobs', prompt=False)

VALIDATOR.option('DEFAULT', 'neo4j_image', validator=validation.file_,
                 default=NEO4J_IMAGE, info='neo4j container image',
                 input_fn=filepath_completion_input, prompt=True)

VALIDATOR.option('DEFAULT', 'redis_image', validator=validation.file_,
                 default=REDIS_IMAGE, info='redis container image',
                 input_fn=filepath_completion_input, prompt=True)

VALIDATOR.option('DEFAULT', 'max_restarts', validator=int, default=3, prompt=False,
                 info='max number of times beeflow will restart a component on failure')

# Workflow Manager
VALIDATOR.section('workflow_manager', info='Workflow manager section.')
# Task manager
VALIDATOR.section('task_manager',
                  info='Task manager configuration and config of container to use.')
VALIDATOR.option('task_manager', 'container_runtime', default='Charliecloud',
                 choices=('Charliecloud', 'Singularity'), prompt=False,
                 info='container runtime to use for configuration')
VALIDATOR.option('task_manager', 'runner_opts', default='', prompt=False,
                 info='special runner options to pass to the runner opts')
VALIDATOR.option('task_manager', 'background_interval', default=5,
                 validator=int, prompt=False,
                 info='interval at which the task manager processes queues and updates states')

# Charliecloud (depends on task_manager::container_runtime == Charliecloud)
VALIDATOR.section('charliecloud', info='Charliecloud configuration section.',
                  depends_on=('task_manager', 'container_runtime', 'Charliecloud'))
VALIDATOR.option('charliecloud', 'image_mntdir', default=join_path('/tmp', USER), prompt=False,
                 info='Charliecloud mount directory', validator=validation.make_dir)
# General job requirements
VALIDATOR.section('job', info='General job requirements.')
VALIDATOR.option('job', 'default_account', validator=lambda val: val.strip(), prompt=True,
                 default='', info='default account to launch jobs with (leave blank if none)')
VALIDATOR.option('job', 'default_time_limit', validator=validation.time_limit, prompt=True,
                 default='', info='default account time limit (leave blank if none)')
VALIDATOR.option('job', 'default_partition', validator=lambda val: val.strip(), prompt=True,
                 default='', info='default partition to run jobs on (leave blank if none)')
VALIDATOR.option('job', 'default_qos', validator=lambda val: val.strip(), prompt=True,
                 default='', info='default qos to run jobs on (leave blank if none)')
VALIDATOR.option('job', 'default_reservation', validator=lambda val: val.strip(), prompt=True,
                 default='', info='default reservation to run jobs on (leave blank if none)')


def validate_chrun_opts(opts):
    """Ensure that chrun_opts don't contain options that'll conflict with BEE."""
    args = opts.split()
    if '--cd' in args or '-c' in args:
        raise ValueError('Initial working directory option (-c or --cd) conflicts with BEE. '
                         'Please make sure that you choose the correct working directory on '
                         'workflow submission.')
    return opts


VALIDATOR.option('charliecloud', 'chrun_opts', default='--home',
                 validator=validate_chrun_opts, prompt=False,
                 info='extra options to pass to ch-run')
VALIDATOR.option('charliecloud', 'setup', default='', prompt=False,
                 info='extra Charliecloud setup to put in a job script')
# Graph Database
VALIDATOR.section('graphdb', info='Main graph database configuration section.')
VALIDATOR.option('graphdb', 'hostname', default='localhost', prompt=False,
                 info='hostname of database')

VALIDATOR.option('graphdb', 'dbpass', default='password', info='password for database',
                 prompt=False)

VALIDATOR.option('graphdb', 'gdb_image_mntdir', default=join_path('/tmp', USER), prompt=False,
                 info='graph database image mount directory', validator=validation.make_dir)
VALIDATOR.option('graphdb', 'sleep_time', validator=int, default=1, prompt=False,
                 info='how long to wait for the graph database to come up (this can take a while, '
                      'depending on the system)')
# Builder
VALIDATOR.section('builder', info='General builder configuration section.')
VALIDATOR.option('builder', 'deployed_image_root', default='/tmp', prompt=False,
                 info='where to deploy container images', validator=validation.make_dir)
VALIDATOR.option('builder', 'container_output_path', default='/tmp', prompt=False,
                 info='container output path', validator=validation.make_dir)
VALIDATOR.option('builder', 'container_archive', prompt=True,
                 default=join_path(DEFAULT_BEE_WORKDIR, 'container_archive'),
                 info='container archive location')
VALIDATOR.option('builder', 'container_type', default='charliecloud',
                 info='container type to use', prompt=False)
# Slurmrestd (depends on DEFAULT:workload_scheduler == Slurm)
VALIDATOR.section('slurm', info='Configuration section for Slurm.',
                  depends_on=('DEFAULT', 'workload_scheduler', 'Slurm'))
VALIDATOR.option('slurm', 'use_commands', validator=validation.bool_,
                 default=(shutil.which('slurmrestd') is None), prompt=False,
                 info='if set, use slurm cli commands instead of slurmrestd')
DEFAULT_SLURMRESTD_SOCK = join_path('/tmp', f'slurm_{USER}_{random.randint(1, 10000)}.sock')

# Scheduler
VALIDATOR.section('scheduler', info='Scheduler configuration section.')
SCHEDULER_ALGORITHMS = ('fcfs', 'backfill', 'sjf')
VALIDATOR.option('scheduler', 'algorithm', default='fcfs', choices=SCHEDULER_ALGORITHMS,
                 info='scheduling algorithm to use', prompt=False)
VALIDATOR.option('scheduler', 'default_algorithm', default='fcfs',
                 choices=SCHEDULER_ALGORITHMS, prompt=False,
                 info=('default algorithm to use'))


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

    def choose_values(self, interactive=False, flux=False):
        """Choose configuration values based on user input."""
        dirname = os.path.dirname(self.fname)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        print(f'Creating a new config: "{self.fname}".')
        print()
        if interactive:
            print_wrap('This will walk you through creating a new configuration for BEE. '
                       'Note that you will only be required to enter values for some '
                       'options. Please take a look at the other options and their '
                       'values before running BEE.')
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
                    print(f'\n## {sec_name}\n')
                    print_wrap(section.info)
                    print()
                    printed = True

                this_default = option.default
                if flux is True and opt_name == 'workload_scheduler':
                    this_default = "Flux"
                    option.prompt = False
                # Check for a default value
                if (not interactive or option.prompt is False) and this_default is not None:
                    value = option.validate(this_default)
                    print(f'Setting option "{opt_name}" to default value "{value}".')
                    print()
                    self.sections[sec_name][opt_name] = value
                    continue

                # Input and validate the value
                value = self._input_loop(opt_name, option)

                print()
                self.sections[sec_name][opt_name] = value
        return self

    def _input_loop(self, opt_name, option):
        """Run the input-validation loop."""
        # Check if there's a special input function (this allows for tab completion)
        input_fn = option.input_fn if option.input_fn is not None else input
        # Start of input loop
        value = None
        while value is None:
            print_wrap(f'{opt_name} - {option.info}')
            if option.choices is not None:
                print(f'(allowed values: {",".join(option.choices)})')
            value = input_fn(f'Enter selection for {opt_name} or\n'
                             + f'leave blank for default ({option.default}): ') or option.default
            # Validate the input
            try:
                option.validate(value)
            except ValueError as err:
                print('ERROR:', err)
                value = None
        return value

    def save(self, interactive=False):
        """Save the config to a file."""
        print()
        print('The following configuration options were chosen:')
        for sec_name, section in self.sections.items():
            print()
            print(f'[{sec_name}]')
            for opt_name in section:
                print(f'{opt_name} = {section[opt_name]}')
        print()
        if interactive:
            ans = input('Would you like to save this config? [y/n] ')
            if ans.lower() != 'y':
                print('Quitting without saving')
                return
        config_utils.write_config(self.fname, self.sections)
        print(70 * '#')
        print('Before running BEE, check defaults in the configuration file:',
              f'\n\t{self.fname}',
              '\n ** See documentation for values you should refrain from editing! **',
              '\n ** Include job options (such as account) required for this system.**')
        print('\n(Try `beeflow config info` to see more about each option)')
        print(70 * '#')


class AlterConfig:
    r"""Class to alter an existing BEE configuration.

    Changes can be made when the class is instantiated, for example:
    AlterConfig(changes={'DEFAULT': {'neo4j_image': '/path/to/neo4j'}})

    Changes can also be made later, for example:
    alter_config = AlterConfig()
    alter_config.change_value('DEFAULT', 'neo4j_image', '/path/to/neo4j')
    """

    def __init__(self, fname=USERCONFIG_FILE, validator=VALIDATOR, changes=None):
        """Load the existing configuration."""
        self.fname = fname
        self.validator = validator
        self.config = None
        self.changes = changes if changes is not None else {}
        self._load_config()

        for sec_name, opts in self.changes.items():
            for opt_name, new_value in opts.items():
                self.change_value(sec_name, opt_name, new_value)

    def _load_config(self):
        """Load the existing configuration file into memory."""
        config = ConfigParser()
        try:
            with open(self.fname, encoding='utf-8') as fp:
                config.read_file(fp)
                self.config = config_utils.filter_and_validate(config, self.validator)
        except FileNotFoundError:
            for section_change in self.changes:
                for option_change in self.changes[section_change]:
                    for opt_name, option in VALIDATOR.options(section_change):
                        if opt_name == option_change:
                            option.default = self.changes[section_change][option_change]
            self.config = ConfigGenerator(self.fname, self.validator).choose_values().sections

    def change_value(self, sec_name, opt_name, new_value):
        """Change the value of a configuration option."""
        if sec_name not in self.config:
            raise ValueError(f'Section {sec_name} not found in the config.')
        if opt_name not in self.config[sec_name]:
            raise ValueError(f'Option {opt_name} not found in section {sec_name}.')

        # Find the correct option from the validator
        options = self.validator.options(sec_name)  # Get all options for the section
        for option_name, option in options:
            if option_name == opt_name:
                # Validate the new value before changing
                option.validate(new_value)
                self.config[sec_name][opt_name] = new_value
                # Track changes in attribute
                if sec_name not in self.changes:
                    self.changes[sec_name] = {}
                self.changes[sec_name][opt_name] = new_value
                return

        raise ValueError(f'Option {opt_name} not found in the validator for section {sec_name}.')

    def save(self):
        """Save the modified configuration back to the file."""
        if os.path.exists(self.fname):
            config_utils.backup(self.fname)
        config_utils.write_config(self.fname, self.config)
        # Print out changes
        print("Configuration saved. The following values were changed:")
        for sec_name, options in self.changes.items():
            for opt_name, new_value in options.items():
                print(f'Section [{sec_name}], Option [{opt_name}] changed to [{new_value}].')


app = typer.Typer(no_args_is_help=True, add_completion=False, cls=NaturalOrderGroup)


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
        print()
        print_wrap(section.info)
        if section.depends_on is not None:
            deps = section.depends_on
            print()
            print_wrap(f'Section required if {deps[0]}::{deps[1]} == "{deps[2]}".')
        print()
        print('Options:')
        for opt_name, option in VALIDATOR.options(sec_name):
            print_wrap(f'* {opt_name} - {option.info}', '  ')
            if option.choices is not None:
                print(f'    * allowed values: {",".join(option.choices)}')
        print()


@app.command()
def new(path: str = typer.Argument(default=USERCONFIG_FILE,
                                   help='Path to new config file'),
        interactive: bool = typer.Option(False, '--interactive', '-i',
                                         help='Whether or not to be prompted'
                                         + ' during config generation'),
        flux: bool = typer.Option(False, '--flux', '-f',
                                  help='Changes default scheduler to Flux')):
    """Create a new config file."""
    if os.path.exists(path):
        if not interactive or check_yes(f'Path "{path}" already exists.\n'
                                        + 'Would you like to save a copy of it?'):
            config_utils.backup(path)
    ConfigGenerator(path, VALIDATOR).choose_values(
        flux=flux,
        interactive=interactive
    ).save(interactive=interactive)


@app.command()
def show(path: str = typer.Argument(default=USERCONFIG_FILE,
                                    help='Path to config file')):
    """Show the contents of bee.conf."""
    if not os.path.exists(path):
        print('The bee.conf does not exist yet. Please run `beeflow config new`.')
        return
    print(f'# {path}')
    with open(path, encoding='utf-8') as fp:
        print(fp.read(), end='')
# Ignore C901: "'ConfigGenerator.choose_values' is too complex" - I disagree, if
#              it's just based on LOC, then there are a number `print()` functions
#              that are increasing the line count
# pylama:ignore=C901
