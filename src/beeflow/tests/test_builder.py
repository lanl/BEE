"""Builder test cases."""


from beeflow.common.config_driver import BeeConfig as bc

bc.init()

from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import Task

### dockerPull
def test_docker_pull():
    task = Task(name='hi',base_command=['hi','hello'],
                     requirements={'DockerRequirement':{'dockerPull':'git.lanl.gov:5050/qwofford/containerhub/lstopo'}},
                 hints=None,
                     workflow_id=42,
                     stdout="output.txt",
                     task_id=1,
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    a.process_docker_pull()
    a.process_docker_pull('git.lanl.gov:5050/trandles/baseimages/centos:7')
    
    task = Task(name='hi',base_command=['hi','hello'],
                     requirements={},
                     hints=None,
                     workflow_id=42,
                     stdout="output.txt",
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    a.process_docker_pull()
    a.process_docker_pull('git.lanl.gov:5050/qwofford/containerhub/lstopo')
    
    task = Task(name='hi',base_command=['hi','hello'],
                     hints=None,
                     requirements=None,
                     workflow_id=42,
                     stdout="output.txt",
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    a.process_docker_pull()
    a.process_docker_pull('git.lanl.gov:5050/qwofford/containerhub/lstopo')
    a.process_docker_pull('git.lanl.gov:5050/qwofford/containerhub/lstopo',force=True)

### dockerFile
def test_docker_file():
    from beeflow.common.build.container_drivers import CharliecloudBuildDriver
    from beeflow.common.wf_data import Task
    task = Task(name='hi',base_command=['hi','hello'],
                     requirements={'DockerRequirement':{'dockerFile':'src/beeflow/data/dockerfiles/Dockerfile.builder_demo',
                                                        'beeflow:containerName':'my_fun_container:sillytag'}},
                     hints=None,
                     workflow_id=42,
                     stdout="output.txt",
                     inputs={},
                     outputs={})
    b = CharliecloudBuildDriver(task)
    b.process_docker_file()
    # ERROR: dockerFile may not be specified without containerName
    b.process_container_name()
    b.process_docker_file()

### dockerImport
def test_docker_import():
    task = Task(name='hi',base_command=['hi','hello'],
                     requirements={},
                     hints=None,
                     workflow_id=42,
                     stdout='output.txt',
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    task = Task(name='hi',base_command=['hi','hello'],
                     requirements={'DockerRequirement':{'dockerImport':'/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz'}},
                     hints=None,
                     workflow_id=42,
                     stdout='output.txt',
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    a.process_docker_import()
    task = Task(name='hi',base_command=['hi','hello'],
                     hints={'DockerRequirement':{'dockerImport':'/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz'}},
                     requirements=None,
                     workflow_id=42,
                     stdout='output.txt',
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    a.process_docker_import()

### dockerOutputDirectory   Needs work
def test_docker_output_dir():
    task = Task(name='hi',base_command=['hi','hello'],
                     hints={'DockerRequirement':{'dockerImport':'/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz'}},
                     requirements=None,
                     workflow_id=42,
                     stdout='output.txt',
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)

    # >>> Container-relative output path is: /
    # >>> a.process_docker_output_directory()
    # >>> '/'
    a.process_docker_output_directory(param_output_directory='/home/<username>')
    # >>> '/home/<username>'
    # Note: Changing the output directory by parameter changes the bc object, but it does NOT over-write the config file.
    a.process_docker_output_directory()
    # >>> '/home/<username>'

### dockerLoad
def test_docker_load():
    task = Task(name='hi',base_command=['hi','hello'],
                     hints={'DockerRequirement':{'dockerLoad':'bogus path'}},
                     requirements=None,
                     workflow_id=42,
                     stdout='output.txt',
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    a.process_docker_load()
    # >>> Charliecloud does not have the concept of a layered image tarball.
    # >>> Did you mean to use dockerImport?
    # >>> 0
    task = Task(name='hi',base_command=['hi','hello'],
                     requirements={'DockerRequirement':{'dockerLoad':'bogus path'}},
                     hints=None,
                     workflow_id=42,
                     stdout='output.txt',
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    a.process_docker_load()
    # >>> Charliecloud does not have the concept of a layered image tarball.
    # >>> Did you mean to use dockerImport?
    # >>> ERROR: dockerLoad specified as requirement.
    # >>> 1

### beeflow:containerName

def test_container_name():
    task = Task(name='hi',base_command=['hi','hello'],
                     hints={'DockerRequirement':{'beeflow:containerName':'my_containerName'}},
                     requirements=None,
                     workflow_id=42,
                     stdout='output.txt',
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    a.process_container_name()
    # INFO: Setting container_name to: my_containerName
    # 0
    task = Task(name='hi',base_command=['hi','hello'],
                     hints=None,
                     requirements=None,
                     workflow_id=42,
                     stdout='output.txt',
                     inputs={},
                     outputs={})
    a = CharliecloudBuildDriver(task)
    a.process_container_name()
    # >>> 1
    ### Add tests for beeflow:copyContainer and beeflow:useContainer
