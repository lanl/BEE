"""Unit tests for the config driver."""

import pytest
from beeflow.common.config_driver import AlterConfig


@pytest.fixture
def sample_config():
    """Sample sections data for testing write_config."""
    return {
        'DEFAULT': {'bee_workdir': '$BEE_WORKDIR', 'workload_scheduler': '$WORKLOAD_SCHEDULER'},
        'task_manager': {'container_runtime': 'Charliecloud', 'runner_opts': ''}
    }


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


def test_change_value_success(mocker, sample_config):
    """Test changing an existing config value."""
    mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')
    alter_config = AlterConfig()
    alter_config.config = sample_config

    mocker.patch("pathlib.Path.mkdir")
    alter_config.change_value("DEFAULT", "bee_workdir", "/new/path")
    assert alter_config.config["DEFAULT"]["bee_workdir"] == "/new/path"


def test_change_value_nonexistent_section(mocker, sample_config):
    """Test changing a value in a nonexistent section raises an error."""
    mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')
    alter_config = AlterConfig()
    alter_config.config = sample_config

    mocker.patch("pathlib.Path.mkdir")
    with pytest.raises(ValueError, match="Section NON_EXISTENT not found in the config."):
        alter_config.change_value("NON_EXISTENT", "some_option", "new_value")


def test_change_value_nonexistent_option(mocker, sample_config):
    """Test changing a nonexistent option raises an error."""
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


def test_change_value_multiple_times(mocker, sample_config):
    """Test changing a config value multiple times and tracking changes."""
    mocker.patch('beeflow.common.config_driver.AlterConfig._load_config')
    alter_config = AlterConfig()
    alter_config.config = sample_config

    mocker.patch("pathlib.Path.mkdir")
    alter_config.change_value("DEFAULT", "bee_workdir", "/path/one")
    alter_config.change_value("DEFAULT", "bee_workdir", "/path/two")
    assert alter_config.config["DEFAULT"]["bee_workdir"] == "/path/two"
    assert alter_config.changes == {"DEFAULT": {"bee_workdir": "/path/two"}}
