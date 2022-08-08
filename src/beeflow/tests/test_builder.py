"""Builder test cases."""
import pytest

from beeflow.common.config_driver import BeeConfig as bc
from beeflow.common.build import BuildError

bc.init()

from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import Task


def test_docker_pull():
    """Test the dockerPull option."""
    task = Task(name='hi', base_command=['hi', 'hello'],
                requirements={'DockerRequirement': {'dockerPull': 'git.lanl.gov:5050/qwofford/containerhub/lstopo'}},
                hints=None,
                workflow_id=42,
                stdout="output.txt",
                task_id=1,
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)
    driver.process_docker_pull()
    driver.process_docker_pull('git.lanl.gov:5050/trandles/baseimages/centos:7')

    task = Task(name='hi', base_command=['hi', 'hello'],
                     requirements={},
                     hints=None,
                     workflow_id=42,
                     stdout="output.txt",
                     inputs={},
                     outputs={})
    driver = CharliecloudBuildDriver(task)
    with pytest.raises(BuildError, match='dockerPull not set'):
        driver.process_docker_pull()

    task = Task(name='hi', base_command=['hi', 'hello'],
                     hints=None,
                     requirements=None,
                     workflow_id=42,
                     stdout="output.txt",
                     inputs={},
                     outputs={})
    driver = CharliecloudBuildDriver(task)
    with pytest.raises(BuildError):
        driver.process_docker_pull()
    driver.process_docker_pull('git.lanl.gov:5050/qwofford/containerhub/lstopo')
    driver.process_docker_pull('git.lanl.gov:5050/qwofford/containerhub/lstopo', force=True)


def test_docker_file():
    """Test the dockerFile option."""
    task = Task(name='hi', base_command=['hi', 'hello'],
                requirements={'DockerRequirement': {'dockerFile': 'src/beeflow/data/dockerfiles/Dockerfile.builder_demo',
                                                    'beeflow:containerName': 'my_fun_container:sillytag'}},
                hints=None,
                workflow_id=42,
                stdout="output.txt",
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)
    driver.process_container_name()
    # ERROR: dockerFile may not be specified without containerName
    driver.process_docker_file()

    task = Task(name='hi', base_command=['hi', 'hello'],
                requirements={'DockerRequirement': {'dockerFile': 'src/beeflow/data/dockerfiles/Dockerfile.builder_demo',
                                                    'beeflow:containerName': 'my_fun_container:sillytag'}},
                hints=None,
                workflow_id=42,
                stdout="output.txt",
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)
    driver.process_container_name()
    driver.process_docker_file()


def test_docker_import():
    """Test the dockerImport option."""
    task = Task(name='hi', base_command=['hi', 'hello'],
                     requirements={},
                     hints=None,
                     workflow_id=42,
                     stdout='output.txt',
                     inputs={},
                     outputs={})
    driver = CharliecloudBuildDriver(task)
    task = Task(name='hi', base_command=['hi', 'hello'],
                requirements={'DockerRequirement': {'dockerImport': '/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz'}},
                hints=None,
                workflow_id=42,
                stdout='output.txt',
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)
    driver.process_docker_import()
    task = Task(name='hi', base_command=['hi', 'hello'],
                hints={'DockerRequirement': {'dockerImport': '/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz'}},
                requirements=None,
                workflow_id=42,
                stdout='output.txt',
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)
    driver.process_docker_import()


def test_docker_output_dir():
    """Test docker output."""
    task = Task(name='hi', base_command=['hi', 'hello'],
                hints={'DockerRequirement': {'dockerImport': '/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz'}},
                requirements=None,
                workflow_id=42,
                stdout='output.txt',
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)

    # >>> Container-relative output path is: /
    # >>> a.process_docker_output_directory()
    # >>> '/'
    driver.process_docker_output_directory(param_output_directory='/home/<username>')
    # >>> '/home/<username>'
    # Note: Changing the output directory by parameter changes the bc object, but it does NOT over-write the config file.
    driver.process_docker_output_directory()
    # >>> '/home/<username>'


def test_docker_load():
    """Test the dockerLoad option."""
    task = Task(name='hi', base_command=['hi', 'hello'],
                hints={'DockerRequirement': {'dockerLoad': 'bogus path'}},
                requirements=None,
                workflow_id=42,
                stdout='output.txt',
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)
    with pytest.raises(BuildError):
        driver.process_docker_load()
    # >>> Charliecloud does not have the concept of a layered image tarball.
    # >>> Did you mean to use dockerImport?
    # >>> 0
    task = Task(name='hi', base_command=['hi', 'hello'],
                requirements={'DockerRequirement': {'dockerLoad': 'bogus path'}},
                hints=None,
                workflow_id=42,
                stdout='output.txt',
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)
    with pytest.raises(BuildError):
        driver.process_docker_load()
    # >>> Charliecloud does not have the concept of a layered image tarball.
    # >>> Did you mean to use dockerImport?
    # >>> ERROR: dockerLoad specified as requirement.
    # >>> 1


def test_container_name():
    """Test the BEE extension option beeflow:containerName."""
    task = Task(name='hi', base_command=['hi', 'hello'],
                hints={'DockerRequirement': {'beeflow:containerName': 'my_containerName'}},
                requirements=None,
                workflow_id=42,
                stdout='output.txt',
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)
    driver.process_container_name()
    # INFO: Setting container_name to: my_containerName
    # 0
    task = Task(name='hi', base_command=['hi', 'hello'],
                hints=None,
                requirements=None,
                workflow_id=42,
                stdout='output.txt',
                inputs={},
                outputs={})
    driver = CharliecloudBuildDriver(task)
    with pytest.raises(BuildError, match='beeflow:containerName: You must specify the containerName or dockerImageId'):
        driver.process_container_name()
    # >>> 1


# TODO: Add tests for beeflow:copyContainer and beeflow:useContainer
def test_use_container():
    """Test the BEE extension option beeflow:useContainer."""

def test_copy_container():
    """Test the BEE extension option beeflow:copyContainer."""
