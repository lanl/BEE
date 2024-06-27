"""Configuration validor tests."""
import pytest
from beeflow.common.config_validator import ConfigValidator, ConfigError


def test_empty():
    """Test an empty config."""
    validator = ConfigValidator(description='empty test case')
    assert validator.validate({}) == {} # noqa (suggestion is wrong for this case)
    # Invalid sections and options should just print a warning rather than fail
    assert validator.validate({'bad_section': {}}) == {} # noqa (suggestion is wrong for this case)
    assert validator.validate({'bad_section': {'bad_option'}}) == {} # noqa (suggestion is wrong for this case)


def test_two():
    """Test a config with two sections."""
    conf = {'section0': {'key0': 'value'}, 'section1': {'key0': '123'}}
    valid_conf = {'section0': {'key0': 'value'}, 'section1': {'key0': 123}}

    validator = ConfigValidator(description='test case of two')
    validator.section('section0', info='some info')
    validator.section('section1', info='some more info')
    validator.option('section0', 'key0', validator=str, info='some config opt')
    validator.option('section1', 'key0', validator=int, info='some config opt')

    assert validator.validate(conf) == valid_conf
    # Test missing sections and values
    with pytest.raises(ConfigError):
        validator.validate({'section1': {'key0': 'abc'}})
    with pytest.raises(ConfigError):
        validator.validate({})
    with pytest.raises(ConfigError):
        validator.validate({'section2': {'key0': 'something'}})


def test_choices():
    """Test a config option that can have a set of choices."""
    validator = ConfigValidator(description='test case for choice-based option')
    validator.section('section0', info='info')
    validator.option('section0', 'choice-key', choices=('A', 'B', 'C'), info='choice-based option')

    assert (validator.validate({'section0': {'choice-key': 'B'}})
            == {'section0': {'choice-key': 'B'}}) # noqa
    with pytest.raises(ConfigError):
        assert validator.validate({'section0': {'choice-key': 'E'}})


def test_depends_on():
    """Test the depends_on relation for sections in a config."""
    validator = ConfigValidator(description='depends on relation test')
    validator.section('one', info='section one')
    validator.option('one', 'key', choices=('A', 'B'), info='choice-based option')
    # Section two depends on one::key == A
    validator.section('two', info='section two', depends_on=('one', 'key', 'A'))
    validator.option('two', 'some-key', info='some other config value dependent on [one] key == A')

    with pytest.raises(ConfigError):
        assert validator.validate({'one': {'key': 'B'}, 'two': {}})
    with pytest.raises(ConfigError):
        validator.validate({'one': {'key': 'A'}})
    assert (validator.validate({'one': {'key': 'A'}, 'two': {'some-key': '123'}})
            == {'one': {'key': 'A'}, 'two': {'some-key': '123'}}) # noqa


def test_depends_on_order():
    """Test that the depends_on relation is not broken by ordering."""
    validator = ConfigValidator(description='depends on relation test')
    # Section two depends on one::key == A
    validator.section('two', info='section two', depends_on=('one', 'key', 'A'))
    validator.option('two', 'some-key', info='some other config value dependent on [one] key == A')
    validator.section('one', info='section one')
    validator.option('one', 'key', choices=('A', 'B'), info='choice-based option')

    # Sections must be listed in dependency order, so if section two depends
    # on section one, then section one must be listed first, then section two
    sections = validator.sections
    assert sections[0][0] == 'one'
    assert sections[1][0] == 'two'


def test_depends_on_validate():
    """Test that validation does not break the depends_on relation."""
    validator = ConfigValidator(description='depends on relation test')
    # Section two depends on one::key == A
    validator.section('two', info='section two', depends_on=('one', 'key', 'A'))
    validator.option('two', 'some-key', info='some other config value dependent on [one] key == A')
    validator.section('one', info='section one')
    validator.option('one', 'key', choices=('A', 'B'), info='choice-based option')

    assert not validator.is_section_valid({'one': {'key': 'B'}}, 'two')
    assert validator.is_section_valid({'one': {'key': 'A'}}, 'two')
    assert validator.is_section_valid({}, 'one')


def test_section_order():
    """Ensure that the order of section insertion is preserved."""
    validator = ConfigValidator(description='section order test')
    validator.section('one', info='section one')
    validator.option('one', 'key-a', info='some option')
    validator.section('two', info='section two')
    validator.option('two', 'key-b', info='some option')

    sections = validator.sections

    assert sections[0][0] == 'one'
    assert sections[1][0] == 'two'


def test_double_definition():
    """Ensure that double definitions of sections and options are not allowed."""
    validator = ConfigValidator(
        description='test case for when code tries to define sections and options twice'
    )

    validator.section('section', info='some section')
    with pytest.raises(ConfigError):
        validator.section('section', info='some section defined twice')

    validator.option('section', 'option', info='some option')
    with pytest.raises(ConfigError):
        validator.option('section', 'option', info='some option defined twice')


def test_missing_section():
    """Test validation of a missing section."""
    validator = ConfigValidator(description='missing section')

    with pytest.raises(ConfigError):
        validator.option('some-section', 'option',
                         info='defining an option, but the section is not defined')


def test_option_default():
    """Test setting a default value for an option."""
    validator = ConfigValidator(description='default option validator')

    validator.section('abc', info='some section')
    validator.option('abc', 'test', info='some option with attributes', validator=int, default=1)

    assert validator.validate({}) == {'abc': {'test': 1}}
    assert validator.validate({'abc': {'test': 3}}) == {'abc': {'test': 3}}
