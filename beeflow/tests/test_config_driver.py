import pytest
from beeflow.tests.mocks import MockAlterConfig

def test_initialization_without_changes():
    """Test initialization without any changes."""
    config = MockAlterConfig()
    assert config.config == {
        "DEFAULT": {
            "bee_workdir": "$BEE_WORKDIR",
            "workload_scheduler": "$WORKLOAD_SCHEDULER"
        }
    }
    assert config.changes == {}

def test_initialization_with_changes():
    """Test initialization with some predefined changes."""
    changes = {"DEFAULT": {"bee_workdir": "/new/path"}}
    config = MockAlterConfig(changes=changes)
    assert config.config["DEFAULT"]["bee_workdir"] == "/new/path"
    assert config.changes == changes

def test_change_value_success():
    """Test changing an existing config value."""
    config = MockAlterConfig()
    config.change_value("DEFAULT", "bee_workdir", "/new/path")
    assert config.config["DEFAULT"]["bee_workdir"] == "/new/path"
    assert config.changes == {"DEFAULT": {"bee_workdir": "/new/path"}}

def test_change_value_nonexistent_section():
    """Test changing a value in a nonexistent section raises an error."""
    config = MockAlterConfig()
    with pytest.raises(ValueError, match="Section NON_EXISTENT not found in the config."):
        config.change_value("NON_EXISTENT", "some_option", "new_value")

def test_change_value_nonexistent_option():
    """Test changing a nonexistent option raises an error."""
    config = MockAlterConfig()
    with pytest.raises(ValueError, match="Option non_existent_option not found in section DEFAULT."):
        config.change_value("DEFAULT", "non_existent_option", "new_value")

def test_save():
    """Test the save function."""
    config = MockAlterConfig()
    assert config.save() == "Configuration saved."

def test_change_value_multiple_times():
    """Test changing a config value multiple times and tracking changes."""
    config = MockAlterConfig()
    config.change_value("DEFAULT", "bee_workdir", "/path/one")
    config.change_value("DEFAULT", "bee_workdir", "/path/two")
    assert config.config["DEFAULT"]["bee_workdir"] == "/path/two"
    assert config.changes == {"DEFAULT": {"bee_workdir": "/path/two"}}

def test_change_value_updates_changes_dict():
    """Test that changes dictionary is updated correctly after multiple changes."""
    config = MockAlterConfig()
    config.change_value("DEFAULT", "bee_workdir", "/updated/path")
    config.change_value("DEFAULT", "workload_scheduler", "new_scheduler")
    assert config.config["DEFAULT"]["bee_workdir"] == "/updated/path"
    assert config.config["DEFAULT"]["workload_scheduler"] == "new_scheduler"
    assert config.changes == {
        "DEFAULT": {
            "bee_workdir": "/updated/path",
            "workload_scheduler": "new_scheduler"
        }
    }
