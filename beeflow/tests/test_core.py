"""Tests for the beeflow client core module."""

import subprocess
from pathlib import Path

import pytest

# Import bee_client before core: core imports bee_client, which in turn
# registers core's typer app, so importing core first hits a circular import
from beeflow.client import bee_client # pylint: disable=W0611
from beeflow.client import core
from beeflow.common import config_driver


def test_load_check_charliecloud_missing(mocker, monkeypatch):
    """Test that a missing ch-run exits cleanly without a traceback."""
    mocker.patch('shutil.which', return_value=None)
    monkeypatch.delenv('MODULESHOME', raising=False)
    with pytest.raises(SystemExit):
        core.load_check_charliecloud()


def test_load_check_charliecloud_no_env_modules(mocker, monkeypatch):
    """Test that a broken/absent module system still exits cleanly."""
    mocker.patch('shutil.which', return_value=None)
    monkeypatch.setenv('MODULESHOME', '/nonexistent/modules')
    with pytest.raises(SystemExit):
        core.load_check_charliecloud()


def test_load_check_charliecloud_broken_install(mocker):
    """Test that a broken Charliecloud install (ch-run fails) exits cleanly."""
    mocker.patch('shutil.which', return_value='/usr/bin/ch-run')
    mocker.patch(
        'subprocess.run',
        side_effect=subprocess.CalledProcessError(127, 'ch-run',
                                                  stderr='missing shared library'),
    )
    with pytest.raises(SystemExit):
        core.load_check_charliecloud()


def test_pull_deps_fresh_config(tmp_path, mocker, monkeypatch):
    """Test that pull-deps bootstraps a new config when none exists."""
    # No config file at all (fresh machine)
    monkeypatch.setattr(config_driver, 'USERCONFIG_FILE',
                        str(tmp_path / 'missing' / 'bee.conf'))
    config_driver.BeeConfig.CONFIG = None
    # Point bee_workdir at tmp_path so the dependency dir cleanup at the end
    # of pull_deps cannot touch a real workdir
    for opt_name, option in config_driver.VALIDATOR.options('DEFAULT'):
        if opt_name == 'bee_workdir':
            monkeypatch.setattr(option, 'default', str(tmp_path / 'workdir'))

    mocker.patch('beeflow.client.core.load_check_charliecloud')

    def fake_pull(ref, tarball):
        """Simulate pulling a container by creating the tarball."""
        Path(tarball).write_text('', encoding='utf-8')

    mocker.patch('beeflow.client.core.pull_to_tar', side_effect=fake_pull)
    build_to_tar = mocker.patch('beeflow.client.core.build_to_tar')

    core.pull_deps(outdir=str(tmp_path / 'images'))

    # The Neo4j image is only built for the neo4j graph database, and the
    # default graph database is sqlite3
    build_to_tar.assert_not_called()

    # The config was created and records the redis image
    conf_file = tmp_path / 'missing' / 'bee.conf'
    assert conf_file.is_file()
    assert 'redis_image' in conf_file.read_text(encoding='utf-8')
