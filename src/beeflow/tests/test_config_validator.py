import sys
import pytest
from beeflow.common.config_validator import ConfigValidator, ConfigError


def test_empty():
    validator = ConfigValidator(description='empty test case')
    assert validator.validate({}) == {}
    # It should not allow any extra keys
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
    # Test missing sections and values
    with pytest.raises(ValueError):
        validator.validate({'section1': {'key0': 'abc'}})
    with pytest.raises(ValueError):
        validator.validate({})
    with pytest.raises(ValueError):
        validator.validate({'section2': {'key0': 'something'}})


def test_choices():
    validator = ConfigValidator(description='test case for choice-based option')
    validator.section('section0', info='info')
    validator.option('section0', 'choice-key', choices=('A', 'B', 'C'), info='choice-based option')

    assert validator.validate({'section0': {'choice-key': 'B'}}) == {'section0': {'choice-key': 'B'}}
    with pytest.raises(ValueError):
        assert validator.validate({'section0': {'choice-key': 'E'}})


def test_depends_on():
    validator = ConfigValidator(description='depends on relation test')
    validator.section('one', info='section one')
    validator.option('one', 'key', choices=('A', 'B'), info='choice-based option')
    # Section two depends on one::key == A
    validator.section('two', info='section two', depends_on=('one', 'key', 'A'))
    validator.option('two', 'some-key', info='some other config value dependent on [one] key == A')

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
