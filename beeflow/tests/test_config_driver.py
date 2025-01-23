"""Unit tests for the config driver."""

import os
import pytest
from beeflow.common.config_driver import AlterConfig, ConfigGenerator, new
from beeflow.common.config_validator import ConfigValidator


# AlterConfig tests
def test_initialization_without_changes(mocker):
    """Test initialization without any changes."""
    mocked_load = mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')

    alter_config = AlterConfig()
    mocked_load.assert_called_once()
    assert alter_config.changes == {}


def test_initialization_with_changes(mocker):
    """Test initialization with some predefined changes."""
    mocked_load = mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')
    mocked_change = mocker.patch('beeflow.common.config_driver.AlterConfig.change_value')

    changes = {"DEFAULT": {"bee_workdir": "/new/path"}}
    alter_config = AlterConfig(changes=changes)
    mocked_load.assert_called_once()
    mocked_change.assert_called_once()
    assert alter_config.changes == changes


def test_change_value_success(mocker):
    """Test changing an existing config value."""
    # Define the config
    sample_config = {
        'DEFAULT': {'bee_workdir': '$BEE_WORKDIR', 'workload_scheduler': '$WORKLOAD_SCHEDULER'},
        'task_manager': {'container_runtime': 'Charliecloud', 'runner_opts': ''}
    }
    mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')
    alter_config = AlterConfig()
    alter_config.config = sample_config

    mocker.patch("pathlib.Path.mkdir")
    alter_config.change_value("DEFAULT", "bee_workdir", "/new/path")
    assert alter_config.config["DEFAULT"]["bee_workdir"] == "/new/path"


def test_change_value_nonexistent_section(mocker):
    """Test changing a value in a nonexistent section raises an error."""
    # Define the config
    sample_config = {
        'DEFAULT': {'bee_workdir': '$BEE_WORKDIR', 'workload_scheduler': '$WORKLOAD_SCHEDULER'},
        'task_manager': {'container_runtime': 'Charliecloud', 'runner_opts': ''}
    }
    mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')
    alter_config = AlterConfig()
    alter_config.config = sample_config

    mocker.patch("pathlib.Path.mkdir")
    with pytest.raises(ValueError, match="Section NON_EXISTENT not found in the config."):
        alter_config.change_value("NON_EXISTENT", "some_option", "new_value")


def test_change_value_nonexistent_option(mocker):
    """Test changing a nonexistent option raises an error."""
    # Define the config
    sample_config = {
        'DEFAULT': {'bee_workdir': '$BEE_WORKDIR', 'workload_scheduler': '$WORKLOAD_SCHEDULER'},
        'task_manager': {'container_runtime': 'Charliecloud', 'runner_opts': ''}
    }
    mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')
    alter_config = AlterConfig()
    alter_config.config = sample_config

    mocker.patch("pathlib.Path.mkdir")
    with pytest.raises(
            ValueError,
            match="Option non_existent_option not found in section DEFAULT."
    ):
        alter_config.change_value("DEFAULT", "non_existent_option", "new_value")


def save(mocker):
    """Test the save function."""
    mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')
    alter_config = AlterConfig()

    mocked_save = mocker.patch('beeflow.common.config_driver.AlterConfig.save')
    alter_config.save()
    mocked_save.assert_called_once()


def test_change_value_multiple_times(mocker):
    """Test changing a config value multiple times and tracking changes."""
    # Define the config
    sample_config = {
        'DEFAULT': {'bee_workdir': '$BEE_WORKDIR', 'workload_scheduler': '$WORKLOAD_SCHEDULER'},
        'task_manager': {'container_runtime': 'Charliecloud', 'runner_opts': ''}
    }
    mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')
    alter_config = AlterConfig()
    alter_config.config = sample_config

    mocker.patch("pathlib.Path.mkdir")
    alter_config.change_value("DEFAULT", "bee_workdir", "/path/one")
    alter_config.change_value("DEFAULT", "bee_workdir", "/path/two")
    assert alter_config.config["DEFAULT"]["bee_workdir"] == "/path/two"
    assert alter_config.changes == {"DEFAULT": {"bee_workdir": "/path/two"}}


@pytest.mark.parametrize("interactive, flux, prompt, expected",
                         [
                             (True, True, False, 'Flux'),
                             (True, False, False, 'default'),
                             (True, True, True, 'Flux'),
                             (True, False, True, 'input'),
                             (False, True, False, 'Flux'),
                             (False, False, False, 'default'),
                         ],
                         )
def test_choose_values(interactive, flux, prompt, expected):
    """Test running choose_values with different flags."""
    validator = ConfigValidator('')
    validator.section('sec', info='')
    validator.option('sec', 'workload_scheduler', info='', default='default',
                     validator=lambda _: _, input_fn=lambda _: 'input', prompt=prompt)
    config_generator = ConfigGenerator('', validator)
    config = config_generator.choose_values(interactive=interactive,
                                            flux=flux).sections
    assert config['sec']['workload_scheduler'] == expected


@pytest.mark.parametrize("interactive, input_val, expected",
                         [
                             (True, 'y', 'bee.conf'),
                             (True, 'n', 'Quitting'),
                             (False, '', 'bee.conf'),
                         ],
                         )
def test_config_generator_save(mocker, tmpdir, capsys, interactive, input_val, expected):
    """Test the ConfigGenerator save function with different flags/input options."""
    mocker.patch('builtins.input', return_value=input_val)
    alter_config = ConfigGenerator('bee.conf', lambda _: _)
    with tmpdir.as_cwd():
        alter_config.save(interactive=interactive)
    captured = capsys.readouterr()
    assert expected in captured.out


@pytest.mark.parametrize("interactive, input_val, expected",
                         [
                             (True, 'y', True),
                             (True, 'n', False),
                             (False, '', True),
                         ],
                         )
def test_config_new(mocker, tmpdir, interactive, input_val, expected):
    """Test creation of new config with different settings."""
    filename = 'bee.conf'
    mocker.patch('builtins.input', return_value=input_val)
    mocker.patch('beeflow.common.config_driver.ConfigGenerator.choose_values')
    mocker.patch('beeflow.common.config_driver.ConfigGenerator.choose_values.save')
    with tmpdir.as_cwd():
        with open(filename, 'w', encoding='utf-8'):
            pass
        new("bee.conf", interactive=interactive)
        assert os.path.exists('bee.conf.1') == expected
