# Build functionality for BEE

The BEE system should launch containerized jobs, and resolve the container runtime environment (RTE) using a combination of CWL hints/requirements and BeeConfig parameters. The steps leading up to the creation of an RTE will be referred to as "build" steps. All build functionality is defined in this directory, but may depend on other components (such as container runtimes)

## Extending build functionality
BEE supports build extensions by offering interfaces and templates for those who wish to utilize build functionality not currently supported in BEE. The BEE build system consists of three major parts:


* ***build_interfaces.py:*** A collection of build interfaces which define interactions between build objects and the components they interact with (eg- task manager, worker, workflow manager, ...)
* ***build_driver.py:*** An abstract class which defines functionality that any build driver must have.
* ***\*_drivers.py:***  A collection of drivers which implement all build drivers of a type. eg- container_drivers.py


## The build interface

All BEE components will access build drivers through an interface, and all build interfaces are defined in `../build_interfaces.py`.

**Static methods:** Static methods implement methods associated with build operations but which are not directly to the build interface object and the specific RTE it provides. Static methods do not require that a build interface object exists in order to run.

### BuildInterfaceTM
The BuildInterfaceTM class is defined in `build_interface.py`. This class defines methods which are useful to interactions with the task manager.

**Object initialization:** A BuildInterfaceTM object will be intialized from a BEE build interface class definition. The build interface object will be instantiated with a Task parameter, which may or may not include a `DockerRequirement` CWL hint or requirement.  
**Object usage:** A BuildInterfaceTM object will get the path to a RTE that it has prepared. A BEE build interface object will also get details about the task that created it, and any tasks that it generates related to build operations.  

## The build driver

A generic build driver is defined as BuildDriver, an abstract class in `build_driver.py`. Any specific build driver must implement these methods in order to exist as a BEE build driver. A specific build driver may extend functionality beyond this interface as needed.

### Container build drivers

All build drivers associated with containers are located in `container_drivers.py`. Container drivers implement the BuildDriver abstract class. Container drivers support the CWL spec. Considerations related to container builds and the CWL spec are addressed in the following section:

Each step in a workflow may include a reference to `DockerRequirement` in the CWL hints or requirements. If the `DockerRequirement` CWL hint is defined, any failure in the container runtime will result in a warning, and the workflow will attempt to run in the default environment. If the `DockerRequirement` CWL requirement is defined, any failure in the container runtime will result in an error and the workflow will terminate unsuccessfully. The `DockerRequirement` entry may include one or more fields:

1. `dockerPull:` Specify a container image to retrieve using the container runtime. This specifies the container name and tag. It does not include the path to the container. dockerPull should be used in combination with a container registery specified by dockerLoad, or a default will be assumed.
2. `dockerLoad:` The HTTP URL associated with the container registry in use. The container runtime requested will be specified by the `<container>://` prefix. dockerLoad must be used in combination with dockerPull, such that dockerPull defines what the required container image is named.
3. `dockerFile:` The path to a container definition file. The builder will fail if `dockerFile` is defined along with `dockerPull` or `dockerLoad`.
4. `dockerImport:` Provide HTTP URL to download and gunzip a Docker image using `docker import`. This should be the path to a compressed image.
5. `beeflow:containerName:` A reference to the image id that will be invoked by the container runtime's `run` or `exec` command. Note that this differs from `dockerPull` slightly, in that `dockerPull` is the image to be acquired. It is possible to pull an image in a workflow stage, and then run an entirely different image by specifying a different `containerName`. If `containerName` is not defined, assume `dockerPull` references the container to run. If `containerName` is specified and image does not exist, error.
6. `dockerOutputDirectory:` Set the designated output directory to a specific location inside the Docker container.


A few examples to use for testing:
## CharliecloudBuildDriver Examples

### dockerPull
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import Task
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
```
### dockerFile
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import Task
task = Task(name='hi',base_command=['hi','hello'],
                 requirements={'DockerRequirement':{'dockerFile':'beeflow/data/dockerfiles/Dockerfile.builder_demo',
                                                    'beeflow:containerName':'my_fun_container:sillytag'}},
                 hints=None,
                 workflow_id=42,
                 stdout="output.txt",
                 inputs={},
                 outputs={})
b = CharliecloudBuildDriver(task)
b.process_docker_file()
ERROR: dockerFile may not be specified without containerName
b.process_container_name()
b.process_docker_file()
```
### dockerImport
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import Task
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
```
### dockerOutputDirectory   Needs work
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import Task
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
```
### dockerLoad
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import Task
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
```
### beeflow:containerName

Note: this is a BEE extension to the CWL spec. CWL uses "dockerImageId as a container name, but that actually refers to the image ID hash, which cannot be produced until after a Docekrfile is built. To work around this problem, we created beeflow:containerName.
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import Task
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
```

### Add tests for beeflow:copyContainer and beeflow:useContainer

