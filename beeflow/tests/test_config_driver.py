"""Unit tests for the config driver."""

import os
import shutil
from pathlib import Path
import pytest
from beeflow.common import config_driver
from beeflow.common.config_driver import AlterConfig, BeeConfig, ConfigGenerator, new
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
    # Setup valid paths for neo4j_image and redis_image
    img_dir = tmpdir.mkdir("img")
    neo4j_path = img_dir.join("neo4j.tar.gz")
    redis_path = img_dir.join("redis.tar.gz")
    neo4j_path.write("")  # Create empty mock tarball
    redis_path.write("")  # Create empty mock tarball

    filename = 'bee.conf'
    mocker.patch('builtins.input', return_value=input_val)
    mocker.patch('beeflow.common.config_driver.ConfigGenerator.choose_values')
    mocker.patch('beeflow.common.config_driver.ConfigGenerator.choose_values.save')
    with tmpdir.as_cwd():
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(
                "[DEFAULT]\n"
                "bee_workdir = .\n"
                "workload_scheduler = Slurm\n"
                f"neo4j_image = {neo4j_path}\n"
                f"redis_image = {redis_path}\n\n"
                "[task_manager]\n"
                "container_runtime = Charliecloud\n"
                "runner_opts = \n\n"
                "[slurm]\n"
                "use_commands = False\n\n"
                "[slurm attributes]\n"
                "attributes = partition,nodes\n"
            )
        new("bee.conf", interactive=interactive)
        assert os.path.exists('bee.conf.1') == expected


def test_init_missing_config_raises(tmp_path):
    """Test that initializing with a missing config file gives a clear error."""
    BeeConfig.CONFIG = None
    with pytest.raises(RuntimeError, match='beeflow config new'):
        BeeConfig.init(userconfig=str(tmp_path / 'missing.conf'))


def test_alter_config_save_does_not_touch_user_config(tmp_path):
    """Test that AlterConfig only writes the file it was loaded from."""
    user_conf = Path(config_driver.USERCONFIG_FILE)
    other_conf = tmp_path / 'other.conf'
    shutil.copy(user_conf, other_conf)
    user_conf_contents = user_conf.read_text(encoding='utf-8')

    alter_config = AlterConfig(fname=str(other_conf),
                               changes={'DEFAULT': {'max_restarts': '7'}})
    alter_config.save()

    # The changed config was written to the file it was loaded from, and the
    # user's config file was left untouched
    assert 'max_restarts = 7' in other_conf.read_text(encoding='utf-8')
    assert user_conf.read_text(encoding='utf-8') == user_conf_contents


# choose_values tests for optional options and option depends_on relations
def test_choose_values_noninteractive_skips_optional(tmp_path):
    """Test that non-interactive choose_values skips unsettable optional options."""
    validator = ConfigValidator('')
    validator.section('sec', info='')
    validator.option('sec', 'req', info='', default='x', prompt=True)
    validator.option('sec', 'opt', info='', default=None, prompt=True, optional=True)

    config = ConfigGenerator(str(tmp_path / 'bee.conf'),
                             validator).choose_values(interactive=False).sections
    assert config['sec']['req'] == 'x'
    assert 'opt' not in config['sec']


def test_choose_values_noninteractive_skips_unmet_depends_on(tmp_path):
    """Test that non-interactive choose_values skips options that don't apply."""
    validator = ConfigValidator('')
    validator.section('sec', info='')
    validator.option('sec', 'mode', info='', default='normal', prompt=True)
    # This option would block config generation (no default and a prompt),
    # but it does not apply in this config context
    validator.option('sec', 'special', info='', default=None, prompt=True,
                     depends_on=('sec', 'mode', 'special'))

    config = ConfigGenerator(str(tmp_path / 'bee.conf'),
                             validator).choose_values(interactive=False).sections
    assert config['sec']['mode'] == 'normal'
    assert 'special' not in config['sec']


def test_choose_values_interactive_optional_blank(tmp_path):
    """Test that interactive choose_values allows leaving optional options unset."""
    validator = ConfigValidator('')
    validator.section('sec', info='')
    validator.option('sec', 'opt', info='', default=None, prompt=True, optional=True,
                     input_fn=lambda _: '')

    config = ConfigGenerator(str(tmp_path / 'bee.conf'),
                             validator).choose_values(interactive=True).sections
    assert 'opt' not in config['sec']


def test_config_new_noninteractive_fresh_machine(tmp_path, monkeypatch):
    """Test that non-interactive config new completes with no images available.

    On machines with no default images in /usr/projects/BEE and no pulled
    images yet, config new must complete without prompting, and the
    resulting config must pass validation.
    """
    # Neutralize validators that would create directories outside tmp_path
    for sec_name, _ in config_driver.VALIDATOR.sections:
        for opt_name, option in config_driver.VALIDATOR.options(sec_name):
            if getattr(option._validator, '__name__', '') in ('make_dir', 'dir_'):
                monkeypatch.setattr(option, '_validator', lambda value: value)

    def fail_input(*args, **kwargs):
        """Fail loudly if config generation unexpectedly prompts for input."""
        raise AssertionError('config new unexpectedly prompted for input')

    monkeypatch.setattr('builtins.input', fail_input)

    conf_file = tmp_path / 'bee.conf'
    monkeypatch.setattr(config_driver, 'USERCONFIG_FILE', str(conf_file))
    # Pass the typer options explicitly since typer.Option objects are truthy
    new(str(conf_file), interactive=False, flux=False, attributes=False)

    assert conf_file.is_file()
    # The generated config passes validation
    BeeConfig.CONFIG = None
    BeeConfig.init(userconfig=str(conf_file))
