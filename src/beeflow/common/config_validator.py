"""Configuration validation."""


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
        # first validate each option
        for sec_name in conf:
            new_conf[sec_name] = {}
            section = conf[sec_name]
            if sec_name not in self._sections:
                raise ValueError('section "{}" is not defined'.format(sec_name))
            # check that this section is valid in this context
            dep = self._sections[sec_name].depends_on
            if not self._validate_section(conf, depends_on=dep):
                raise ValueError(
                    "section '%s' requires that %s::%s == '%s'"
                    % (sec_name, dep[0], dep[1], dep[2])
                )
            # validate each option
            for opt_name in section:
                key = (sec_name, opt_name)
                if key not in self._options:
                    raise ValueError(
                        "option '{}' in section '{}' is not defined".format(opt_name, sec_name)
                    )
                option = self._options[key]
                try:
                    new_conf[sec_name][opt_name] = option.validate(section[opt_name])
                except ValueError as ve:
                    raise ValueError(
                        '{}::{}: {}'.format(sec_name, opt_name, ve.args[0])
                    ) from None
        # then check required options
        for key in self._options:
            if not self._validate_section(conf, self._sections[key[0]].depends_on):
                # skip invalid sections
                continue
            if self._options[key].required and (key[0] not in conf or key[1] not in conf[key[0]]):
                raise ValueError(
                    "option '%s' in section '%s' is required but has not been set"
                    % (key[1], key[0])
                )

        # Set of (sec_name, opt_name) pairs for which defaults have already
        # been set, or are in the process of being set.
        done = set()

        def set_default(sec_name, opt_name):
            """Set a default value in the new_conf."""
            if sec_name not in new_conf:
                new_conf[sec_name] = {}
            if sec_name not in conf or opt_name not in conf[sec_name]:
                # try to call a default function
                try:
                    new_conf[sec_name][opt_name] = self._options[key].default(inst)
                except TypeError:
                    new_conf[sec_name][opt_name] = self._options[key].default

        class ConfigInstance:
            """Special class used for setting defaults."""

            def get(self, sec_name, opt_name):
                """Get a config value."""
                if (sec_name not in new_conf or opt_name not in new_conf[sec_name]):
                    if (sec_name, opt_name) not in done:
                        done.add((sec_name, opt_name))
                        set_default(sec_name, opt_name)
                    else:
                        raise ValueError(
                            'there appears to be a default dependency cycle for option '
                            f'{sec_name}::{opt_name}'
                        )
                return new_conf[sec_name][opt_name]

        # special config instance for default functions
        inst = ConfigInstance()

        # finally set defaults
        for key in self._options:
            if not self._validate_section(conf, self._sections[key[0]].depends_on):
                # skip invalid sections
                continue
            set_default(key[0], key[1])
        return new_conf

    def _validate_section(self, conf, depends_on):
        """Ensure that this section is valid in this context (check depends relations)."""
        if depends_on is None:
            return True
        if depends_on[0] not in conf or depends_on[1] not in conf[depends_on[0]]:
            # try and get the default
            value = self._options[(depends_on[0], depends_on[1])].default
        else:
            value = conf[depends_on[0]][depends_on[1]]
        # value must match for the section to be valid
        return value == depends_on[2]

    def section(self, sec_name, info, depends_on=None):
        """Define a configuration section."""
        if sec_name in self._sections:
            raise ConfigError("section '{}' has already been defined".format(sec_name))
        self._sections[sec_name] = ConfigSection(info, depends_on=depends_on)
        # save insertion order
        self._section_order.append(sec_name)

    def option(self, sec_name, opt_name, *args, **kwargs):
        """Define a configuration option."""
        if sec_name not in self._sections:
            raise ConfigError("section '{}' has not been defined".format(sec_name))
        key = (sec_name, opt_name)
        if key in self._options:
            raise ConfigError(
                "option '{}' in section '{}' has already been defined".format(opt_name, sec_name)
            )
        try:
            self._options[key] = ConfigOption(*args, **kwargs)
        except ConfigError as ce:
            raise ConfigError('{}::{}: {}'.format(sec_name, opt_name, ce.args[0])) from None

    @property
    def sections(self):
        """Return all sections in order as list of tuples (sec_name, section)."""
        return [(sec_name, self._sections[sec_name]) for sec_name in self._section_order]

    def options(self, sec_name):
        """Return all options for a given section."""
        return [(key[1], self._options[key]) for key in self._options if key[0] == sec_name]


class ConfigSection:
    """Config section."""

    def __init__(self, info, depends_on=None):
        """Config section constructor."""
        self.info = info
        # (sec_name, key, value)
        self.depends_on = depends_on


class ConfigOption:
    """Config option/validation class."""

    def __init__(self, info, validator=str, required=False, default=None,
                 choices=None, attrs=None):
        """Construct the config option class."""
        self.required = required
        self.info = info
        if choices is not None and not required and default not in choices:
            raise ConfigError(
                "default '%s' is not in the allowed choices %s" % (default, choices)
            )
        self.default = default
        self.choices = choices
        # attrs is designed to hold any extra attribute that could be useful
        self.attrs = attrs
        self._validator = validator

    def validate(self, value):
        """Validate the value and return it."""
        if self.choices is not None:
            if value not in self.choices:
                raise ValueError("value must be one of {}; found '{}'".format(self.choices, value))
            return value
        return self._validator(value)
