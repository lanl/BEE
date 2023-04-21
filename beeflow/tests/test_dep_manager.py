"""Unit tests for dependency manager."""

import io
import os
import tempfile

import pytest
from beeflow.wf_manager.common import dep_manager


def test_check_container_runtime(mocker):
    """Test the check container runtime function."""
    mocker.patch('shutil.which', return_value='have_charliecloud')
    dep_manager.check_container_runtime()
    with pytest.raises(dep_manager.NoContainerRuntime):
        mocker.patch('shutil.which', return_value=None)
        dep_manager.check_container_runtime()


def test_create_image(mocker):
    mocker.patch('shutil.which', return_value='have_charliecloud')
    mocker.patch('subprocess.run', return_value=True)
    mocker.patch('os.makedirs', return_value=True)
    dep_manager.create_image()


def test_setup_gdb_configs(mocker):
    mocker.patch('os.makedirs', return_value=True)
    mocker.patch('shutil.copyfile', return_value=True)
    pass



def test_create_image_no_crt(mocker):
    """Test creating an image when there is no container runtime. 
       Should return an exception.
    """
    mocker.patch('shutil.which', return_value=None)
    mocker.patch('subprocess.run', return_value=True)
    mocker.patch('os.makedirs', return_value=True)
    with pytest.raises(dep_manager.NoContainerRuntime):
        dep_manager.create_image()


def test_start_gdb_noreexecute(mocker):
    """Test start gdb function."""
    # Don't want the side effects of this command
    mocker.patch('beeflow.wf_manager.common.dep_manager.setup_gdb_configs', 
                 return_value=True)
    # Need to mock this in case the tests are run before the config is setup
    mocker.patch('beeflow.wf_manager.common.dep_manager.setup_gdb_configs', 
                 return_value=True)

    mocker.patch('beeflow.common.config_driver.BeeConfig.get', )
    with tempfile.TemporaryDirectory() as mount_dir:
        bolt_port = 8940
        http_port = 8950
        https_port = 8960
        dep_manager.start_gdb(mount_dir, bolt_port, http_port, https_port, 
                              reexecute=True)

        

#def test_make_dep_dir():
#    pass
#
#
#def test_get_dep_dir():
#    pass
#
#
#def test_get_container_dir():
#    pass
#
#
#def test_check_container_dir():
#    pass
#
#
#def test_setup_gdb_mounts():
#    pass
#
#
#def test_setup_gdb_configs():
#    pass
#
#
#def test_create_image():
#    pass
#
#
#def test_start_gdb():
#    pass
#
#
#def test_wait_gdb():
#    pass
#
#
#def test_remove_gdb():
#    pass
#
#
#def test_kill_gdb():
#    """Fork a process. Kill it and cofnirm it was killed."""
#    pid = os.fork()
#    if pid == 0:
#        real_pid = os.getpid()
#        print(f'Pid is {real_pid}')
#        assert False
#    pass
