import pytest
import os
from beeflow.common.config_utils import filter_and_validate, write_config, backup


@pytest.fixture
def sample_config():
    """Sample sections data for testing write_config."""
    return {
        'DEFAULT': {'key1': 'value1', 'key2': 'value2'},
        'Section1': {'key3': 'value3', 'key4': 'value4'}
    }


@pytest.fixture
def temp_file(tmp_path):
    """Temporary file for writing configurations."""
    return tmp_path / "test_config.ini"


class ValidatorMock:
    """Simple mock class for validator."""
    def __init__(self):
        self._called_with = None
        self.return_value = True

    def validate(self, config):
        self._called_with = config
        return self.return_value

    def called_with(self):
        return self._called_with


def test_filter_and_validate(sample_config):
    """Test filtering and validating configuration."""
    # Append key-value pair that will need to be filtered
    sample_config['Section2'] = {'key2': 'new_value', 'key5': 'value5'}

    # Run the function
    mocked_validator = ValidatorMock()
    result = filter_and_validate(sample_config, mocked_validator)

    # Check that the validator was called with the correct filtered config
    expected_filtered_config = {
        'DEFAULT': {'key1': 'value1', 'key2': 'value2'},
        'Section1': {'key3': 'value3', 'key4': 'value4'},
        'Section2': {'key5': 'value5'}
    }
    assert mocked_validator.called_with() == expected_filtered_config

    # Ensure the function returns the validator's return value
    assert result is True


def test_write_config(temp_file, sample_config):
    """Test writing the configuration to a file."""
    # Write the config to a file
    write_config(temp_file, sample_config)

    # Verify file contents
    with open(temp_file, 'r', encoding='utf-8') as fp:
        content = fp.read()

    expected_content = (
        "# BEE Configuration File\n\n"
        "[DEFAULT]\n"
        "key1 = value1\n"
        "key2 = value2\n\n"
        "[Section1]\n"
        "key3 = value3\n"
        "key4 = value4\n"
    )
    assert content == expected_content


def test_write_config_file_not_found(capfd):
    """Test handling of FileNotFoundError in write_config by capturing output."""
    write_config('/invalid/path/config.ini', {'Section': {'key': 'value'}})

    # Capture the printed output
    captured = capfd.readouterr()
    assert "Configuration file does not exist!" in captured.out


def test_backup(temp_file):
    """Test backing up a configuration file."""
    # Create a temporary config file
    temp_file.write_text("sample configuration content")

    # Run the backup function
    backup(temp_file)

    # Check if a backup file was created
    backup_file = f"{temp_file}.1"
    assert os.path.exists(backup_file)

    # Verify that the backup file has the correct content
    with open(backup_file, 'r', encoding='utf-8') as fp:
        content = fp.read()
    assert content == "sample configuration content"


def test_backup_multiple(temp_file):
    """Test that backup increments the backup file number correctly."""
    temp_file.write_text("sample configuration content")

    # Create multiple backups
    backup(temp_file)
    backup(temp_file)
    backup(temp_file)

    # Verify that the third backup file is created
    backup_file_3 = f"{temp_file}.3"
    assert os.path.exists(backup_file_3)
