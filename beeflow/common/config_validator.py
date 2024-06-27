"""Config validation code."""

from beeflow.common import log as bee_logging

log = bee_logging.setup(__name__)


class ConfigError(Exception):
    """Configuration error class."""


class ConfigValidator:
    """Config validation/schema class for managing configuration."""

    def __init__(self, description):
        """Construct the config validator."""
        self.description = description
        self._section_order = []
        self._sections = {}
        self._options = {}

    def validate(self, conf):
        """Validate a config and return a new config with defaults and values converted."""
        new_conf = {}
        errors = []

        self._validate_existing_options(conf, new_conf, errors)
        self._check_required_options(conf, new_conf, errors)

        # Bundle up all the errors into one exception
        if errors:
            message = ['Config validation failed:\n']
            message.extend(f'    * {error}\n' for error in errors)
            raise ConfigError(''.join(message))

        return new_conf

    def _validate_existing_options(self, conf, new_conf, errors):
        """Validate existing options within the config."""
        # First validate each option
        for sec_name in conf:
            section = conf[sec_name]
            if sec_name not in self._sections:
                log.warning(f'config contains invalid section "{sec_name}"')
                continue
            new_conf[sec_name] = {}
            # Check that this section is valid in this context
            dep = self._sections[sec_name].depends_on
            if not self._validate_section(conf, depends_on=dep):
                errors.append(
                    f"section '{sec_name}' requires that {dep[0]}::{dep[1]} == '{dep[2]}'"
                )
                continue
            # Validate each option
            for opt_name in section:
                key = (sec_name, opt_name)
                if key not in self._options:
                    log.warning(f"option {sec_name}::{opt_name} is not a valid option")
                    continue
                option = self._options[key]
                try:
                    new_conf[sec_name][opt_name] = option.validate(section[opt_name])
                except ValueError as err:
                    errors.append(f'{sec_name}::{opt_name}: {err.args[0]}')

    def _check_required_options(self, conf, new_conf, errors):
        """Check for required options and set defaults as necessary."""
        # Then check required options
        for sec_name, opt_name in self._options:
            key = (sec_name, opt_name)
            if not self._validate_section(conf, self._sections[sec_name].depends_on):
                # Skip invalid sections
                continue
            if sec_name not in conf or opt_name not in conf[sec_name]:
                default = self._options[key].default
                if default is None:
                    errors.append(
                        f'option {sec_name}::{opt_name} is required but has not been set'
                    )
                    continue
                # Set the default, but warn the user
                log.warning(f'option {sec_name}::{opt_name} is missing, setting to default '
                            f'"{default}"; please check that that is correct and update the '
                            'config')
                if sec_name not in new_conf:
                    new_conf[sec_name] = {}
                new_conf[sec_name][opt_name] = default

    def _validate_section(self, conf, depends_on):
        """Ensure that this section is valid in this context (check depends relations)."""
        if depends_on is None:
            return True
        if depends_on[0] not in conf or depends_on[1] not in conf[depends_on[0]]:
            return False
        # Value must match for the section to be valid
        return conf[depends_on[0]][depends_on[1]] == depends_on[2]

    def is_section_valid(self, cur_conf, sec_name):
        """Determine if given the current configuration, sec_name is valid.

        sec_name is assumed to be the name of a valid section.
        """
        depends_on = self._sections[sec_name].depends_on
        return self._validate_section(cur_conf, depends_on)

    def section(self, sec_name, info, depends_on=None):
        """Define a configuration section."""
        if sec_name in self._sections:
            raise ConfigError(f"section '{sec_name}' has already been defined")
        self._sections[sec_name] = ConfigSection(info, depends_on=depends_on)
        # Save insertion order
        self._section_order.append(sec_name)

    def option(self, sec_name, opt_name, *args, **kwargs):
        """Define a configuration option."""
        if sec_name not in self._sections:
            raise ConfigError(f"section '{sec_name}' has not been defined")
        key = (sec_name, opt_name)
        if key in self._options:
            raise ConfigError(f'option {sec_name}::{opt_name} has already been defined')
        try:
            self._options[key] = ConfigOption(*args, **kwargs)
        except ConfigError as err:
            raise ConfigError(f'{sec_name}::{opt_name}: {err.args[0]}') from None

    @property
    def sections(self):
        """Return all sections in order as list of tuples (sec_name, section)."""
        sec_names = list(self._section_order)
        s = set()
        order = []
        # Ensure dependency ordering
        for sec_name in sec_names:
            if sec_name in s:
                continue
            section = self._sections[sec_name]
            depends_on = section.depends_on
            if depends_on is not None and depends_on[0] not in s:
                s.add(depends_on[0])
                order.append((depends_on[0], self._sections[depends_on[0]]))
            s.add(sec_name)
            order.append((sec_name, section))
        return order

    def options(self, sec_name):
        """Return all options for a given section."""
        return [(key[1], value) for key, value in self._options.items() if key[0] == sec_name]


class ConfigSection:
    """Config section."""

    def __init__(self, info, depends_on=None):
        """Config section constructor."""
        self.info = info
        # (sec_name, key, value)
        self.depends_on = depends_on


class ConfigOption:
    """Config option/validation class."""

    def __init__(self, info, validator=str, choices=None, default=None, input_fn=None):
        """Construct the config option class."""
        self.info = info
        self.choices = choices
        # Default value, if None the option is required
        self.default = default
        # Function used to set the option from user input at config generation time
        self.input_fn = input_fn
        self._validator = validator

    def validate(self, value):
        """Validate the value and return it."""
        if self.choices is not None:
            if value not in self.choices:
                raise ValueError(f"value must be one of {self.choices}; found '{value}'")
            return value
        return self._validator(value)
