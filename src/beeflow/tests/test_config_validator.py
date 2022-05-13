import sys
import pytest
from beeflow.common.config_validator import ConfigValidator, ConfigError


def test_empty():
    validator = ConfigValidator(description='empty test case')
    assert validator.validate({}) == {}
    # it should not allow any extra keys
    with pytest.raises(ValueError):
        validator.validate({'key': {}})


def test_two():
    conf = {'section0': {'key0': 'value'}, 'section1': {'key0': '123'}}
    valid_conf = {'section0': {'key0': 'value'}, 'section1': {'key0': 123}}

    validator = ConfigValidator(description='test case of two')
    validator.section('section0', info='some info')
    validator.section('section1', info='some more info')
    validator.option('section0', 'key0', validator=str, info='some config opt')
    validator.option('section1', 'key0', validator=int, info='some config opt')

    assert validator.validate(conf) == valid_conf
    with pytest.raises(ValueError):
        validator.validate({'section1': {'key0': 'abc'}})


def test_required():
    conf = {'section0': {'key0': '123'}}

    validator = ConfigValidator(description='test case for required options')
    validator.section('section0', info='some more info')
    validator.option('section0', 'key0', required=True, info='test value')

    assert validator.validate(conf) == conf
    with pytest.raises(ValueError):
        validator.validate({})
    with pytest.raises(ValueError):
        validator.validate({'section0': {}})


def test_choices():
    validator = ConfigValidator(description='test case for choice-based option')
    validator.section('section0', info='info')
    validator.option('section0', 'choice-key', choices=('A', 'B', 'C'), default='C', info='choice-based option')

    assert validator.validate({}) == {'section0': {'choice-key': 'C'}}
    assert validator.validate({'section0': {'choice-key': 'B'}}) == {'section0': {'choice-key': 'B'}}
    with pytest.raises(ValueError):
        assert validator.validate({'section0': {'choice-key': 'E'}})

def test_choices_default():
    validator = ConfigValidator(description='test case for choice-based option')
    validator.section('section0', info='info')
    # adding a choice-based option without a default should raise a runtime error
    with pytest.raises(ConfigError):
        validator.option('section0', 'choice-key1', choices=('A', 'B', 'C'), info='choice-based option')
    # adding a choice-based option with a bad default should also raise an error
    with pytest.raises(ConfigError):
        validator.option('section0', 'choice-key2', choices=('A', 'B', 'C'), default='X', info='choice-based option')
    # but if the option is required, and there is no default, then everything is ok
    validator.option('section0', 'required-choice', required=True, choices=('1', '2', '3'), info='required choice')

def test_defaults():
    validator = ConfigValidator(description='test case for defaults')
    validator.section('a', info='section a')
    validator.option('a', 'key', default='something', info='section with default value')

    assert validator.validate({'a': {'key': '123'}}) == {'a': {'key': '123'}}
    assert validator.validate({'a': {}}) == {'a': {'key': 'something'}}
    assert validator.validate({}) == {'a': {'key': 'something'}}


def test_depends_on():
    validator = ConfigValidator(description='depends on relation test')
    validator.section('one', info='section one')
    validator.option('one', 'key', choices=('A', 'B'), default='B', info='choice-based option')
    # section two depends on one::key == A
    validator.section('two', info='section two', depends_on=('one', 'key', 'A'))
    validator.option('two', 'some-key', required=True, info='some other config value dependent on [one] key == A')

    assert validator.validate({}) == {'one': {'key': 'B'}}
    with pytest.raises(ValueError):
        assert validator.validate({'one': {'key': 'B'}, 'two': {}})
    with pytest.raises(ValueError):
        validator.validate({'one': {'key': 'A'}})
    validator.validate({'one': {'key': 'A'}, 'two': {'some-key': '123'}}) == {'one': {'key': 'A'}, 'two': {'some-key': '123'}}


def test_double_definition():
    validator = ConfigValidator(description='test case for when code tries to define sections and options twice')

    validator.section('section', info='some section')
    with pytest.raises(ConfigError):
        validator.section('section', info='some section defined twice')

    validator.option('section', 'option', info='some option')
    with pytest.raises(ConfigError):
        validator.option('section', 'option', info='some option defined twice')


def test_missing_section():
    validator = ConfigValidator(description='missing section')

    with pytest.raises(ConfigError):
        validator.option('some-section', 'option', info='defining an option, but the section is not defined')


def test_option_attr():
    validator = ConfigValidator(description='option with attribute')

    validator.section('abc', info='some section')
    validator.option('abc', 'test', info='some option with attributes', attrs={'key': 1})

    opt_name, option = validator.options('abc')[0]
    assert opt_name == 'test'
    assert option.attrs == {'key': 1}
