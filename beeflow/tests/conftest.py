"""Shared pytest fixtures and hooks for the BEE test suite."""

import shutil
import tempfile
from pathlib import Path

import pytest

from beeflow.common import config_driver


def _write_test_config(dirpath):
    """Write a minimal BEE config file into dirpath and return its path.

    The config points the workdir and the (dummy) dependency images into
    dirpath so that nothing outside of the test directories is touched.
    """
    dirpath = Path(dirpath)
    img_dir = dirpath / 'img'
    img_dir.mkdir(parents=True, exist_ok=True)
    neo4j_image = img_dir / 'neo4j.tar.gz'
    redis_image = img_dir / 'redis.tar.gz'
    neo4j_image.write_text('')
    redis_image.write_text('')
    workdir = dirpath / 'workdir'
    workdir.mkdir(exist_ok=True)
    conf = dirpath / 'bee.conf'
    conf.write_text(
        '[DEFAULT]\n'
        f'bee_workdir = {workdir}\n'
        'workload_scheduler = Slurm\n'
        f'neo4j_image = {neo4j_image}\n'
        f'redis_image = {redis_image}\n\n'
        '[task_manager]\n'
        'container_runtime = Charliecloud\n\n'
        '[slurm]\n'
        'use_commands = False\n'
    )
    return str(conf)


_SESSION_CONFIG_DIR = None


def pytest_configure():
    """Point the BEE config at a temporary file before test collection.

    Importing some BEE modules initializes the config, so the redirection has
    to happen before test modules are imported; the isolate_bee_config
    fixture below then re-isolates the config for each individual test. This
    ensures the test suite never reads, prompts for, or rewrites the user's
    real ~/.config/beeflow/bee.conf.
    """
    global _SESSION_CONFIG_DIR
    _SESSION_CONFIG_DIR = tempfile.mkdtemp(prefix='bee-test-config-')
    config_driver.USERCONFIG_FILE = _write_test_config(_SESSION_CONFIG_DIR)


def pytest_unconfigure():
    """Remove the temporary config directory."""
    if _SESSION_CONFIG_DIR is not None:
        shutil.rmtree(_SESSION_CONFIG_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def isolate_bee_config(tmp_path):
    """Isolate the BEE configuration from other tests and the user config."""
    # Use a subdirectory of tmp_path to avoid clashing with directories that
    # individual tests create in their own tmpdir (e.g. tmpdir.mkdir("img"))
    conf = _write_test_config(tmp_path / 'bee-config')
    old_file = config_driver.USERCONFIG_FILE
    old_config = config_driver.BeeConfig.CONFIG
    config_driver.USERCONFIG_FILE = conf
    config_driver.BeeConfig.CONFIG = None
    yield
    config_driver.USERCONFIG_FILE = old_file
    config_driver.BeeConfig.CONFIG = old_config
