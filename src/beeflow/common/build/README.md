# Build functionality for BEE

The BEE system should launch containerized jobs, and resolve the container RTE using a combination of CWL hints/requirements and BeeConfig parameters. The steps leading up to the creation of an RTE will be referred to as "build" steps. All build functionality is defined in this directory, but may depend on other components (such as container runtimes)

## Extending build functionality
BEE supports build extensions by offering interfaces and templates for those who wish to utilize build functionality not currently supported in BEE. The BEE build system consists of three major parts:  


* ***build_interfaces.py:*** A collection of build interfaces which define interactions between build objects and the components they interact with (eg- task manager, worker, workflow manager, ...)
* ***build_driver.py:*** An abstract class which defines functionality that any build driver must have.
* ***\*_drivers.py:***  A collection of drivers which implement all build drivers of a type. eg- container_drivers.py


## The build interface

All BEE components will access build drivers through an interface, and all build interfaces are defined in `build_interfaces.py`.

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
4. `dockerImport:` Provide HTTP URL to download and gunzip a Docker images using `docker import`. This should be the path to a compressed image. 
5. `dockerImageId:` A reference to the image id that will be invoked by the container runtime's `run` or `exec` command. Note that this differs from `dockerPull` slightly, in that `dockerPull` is the image to be acquired. It is possible to pull an image in a workflow stage, and then run an entirely different image by specifying a different `dockerImageId`. If `dockerImageId` is not defined, assume `dockerPull` references the container to run. If `dockerImageId` is specified and image does not exist, error.
6. `dockerOutputDirectory:` Set the designated output directory to a specific location inside the Docker container.


A few examples to use for testing:
## CharliecloudBuildDriver Examples
### dockerPull
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import BuildTask
task = BuildTask(name='hi',command=['hi','hello'],
                 requirements={'DockerRequirement':{'dockerPull':'git.lanl.gov:5050/qwofford/containerhub/lstopo'}},
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
a.dockerPull()
a.dockerPull('git.lanl.gov:5050/trandles/baseimages/centos:7')

task = BuildTask(name='hi',command=['hi','hello'],
                 requirements={},
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
a.dockerPull()
a.dockerPull('git.lanl.gov:5050/qwofford/containerhub/lstopo')

task = BuildTask(name='hi',command=['hi','hello'],
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
a.dockerPull()
a.dockerPull('git.lanl.gov:5050/qwofford/containerhub/lstopo')
a.dockerPull('git.lanl.gov:5050/qwofford/containerhub/lstopo',force=True)
```
### dockerFile
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import BuildTask
task = BuildTask(name='hi',command=['hi','hello'],
                 requirements={'DockerRequirement':{'dockerFile':'FROM git.lanl.gov:5050/trandles/baseimages/centos:7\nCMD cat /etc/centos-release',
                                                    'dockerImageId':'my_fun_container:sillytag'}},
                 subworkflow=None,
                 inputs={},
                 outputs={})
b = CharliecloudBuildDriver(task)
b.dockerFile()
```
### dockerImport
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import BuildTask
task = BuildTask(name='hi',command=['hi','hello'],
                 requirements={},
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
# When a "builder" entry does not exist in bee.conf
# >>> Build cache directory is: /yellow/users/qwofford/.beeflow/build_cache
# >>> Config file is missing builder section.
# >>> Assuming deployed image root is /var/tmp/qwofford/beeflow
# >>> Wrote deployed image root to user BeeConfig file.
# >>> Deployed image root directory is: /var/tmp/qwofford/beeflow
# When a "builder entry does exist in bee.conf
# >>> Build cache directory is: /yellow/users/qwofford/.beeflow/build_cache
# >>> Deployed image root directory is: /var/tmp/qwofford/beeflow
task = BuildTask(name='hi',command=['hi','hello'],
                 requirements={'DockerRequirement':{'dockerImport':'/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz'}},
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
a.dockerImport()
# >>> CompletedProcess(args='ch-tar2dir /usr/projects/beedev/neo4j-3-5-17-ch.tar.gz /var/tmp/qwofford/beeflow/', returncode=0, stdout=b'/var/tmp/qwofford/beeflow//neo4j-3-5-17-ch unpacked ok\n', stderr=b'replacing existing image /var/tmp/qwofford/beeflow//neo4j-3-5-17-ch\n')
task = BuildTask(name='hi',command=['hi','hello'],
                 hints={'DockerRequirement':{'dockerImport':'/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz'}},
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
a.dockerImport()
# >>> CompletedProcess(args='ch-tar2dir /usr/projects/beedev/neo4j-3-5-17-ch.tar.gz /var/tmp/qwofford/beeflow/', returncode=0, stdout=b'/var/tmp/qwofford/beeflow//neo4j-3-5-17-ch unpacked ok\n', stderr=b'replacing existing image /var/tmp/qwofford/beeflow//neo4j-3-5-17-ch\n')
```
### dockerOutputDirectory
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import BuildTask
task = BuildTask(name='hi',command=['hi','hello'],
                 hints={'DockerRequirement':{'dockerImport':'/usr/projects/beedev/neo4j-3-5-17-ch.tar.gz'}},
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
# >>> Build cache directory is: /yellow/users/qwofford/.beeflow/build_cache
# >>> Deployed image root directory is: /var/tmp/qwofford/beeflow
# >>> Container-relative output path is: /
# >>> a.dockerOutputDirectory()
# >>> '/'
a.dockerOutputDirectory(param_output_directory='/home/qwofford')
# >>> '/home/qwofford'
# Note: Changing the output directory by parameter changes the bc object, but it does NOT over-write the config file.
a.dockerOutputDirectory()
# >>> '/home/qwofford'
```
### dockerLoad
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import BuildTask
task = BuildTask(name='hi',command=['hi','hello'],
                 hints={'DockerRequirement':{'dockerLoad':'bogus path'}},
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
a.dockerLoad()
# >>> Charliecloud does not have the concept of a layered image tarball.
# >>> Did you mean to use dockerImport?
# >>> 0
task = BuildTask(name='hi',command=['hi','hello'],
                 requirements={'DockerRequirement':{'dockerLoad':'bogus path'}},
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
a.dockerLoad()
# >>> Charliecloud does not have the concept of a layered image tarball.
# >>> Did you mean to use dockerImport?
# >>> ERROR: dockerLoad specified as requirement.
# >>> 1
```
### dockerImageId
```
from beeflow.common.build.container_drivers import CharliecloudBuildDriver
from beeflow.common.wf_data import BuildTask
task = BuildTask(name='hi',command=['hi','hello'],
                 hints={'DockerRequirement':{'dockerImageId':'my_imageid'}},
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
a.dockerImageId()
# >>> 'my_imageid'
a.dockerImageId(param_imageid='another_imageid')
# >>> 'another_imageid'
a.dockerImageId()
# >>> 'my_imageid'
task = BuildTask(name='hi',command=['hi','hello'],
                 subworkflow=None,
                 inputs={},
                 outputs={})
a = CharliecloudBuildDriver(task)
a.dockerImageId()
# >>> 1
a.dockerImageId(param_imageid='another_imageid')
# >>> 'another_imageid'
a.dockerImageId()
# >>> 'another_imageid'
```
