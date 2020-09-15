# Build functionality for BEE

The BEE system should launch containerized or baremetal jobs. The steps leading up to the execution environment will be referred to as "build" steps. All build functionality is defined here, but may depend on other components (such as container runtimes).

**Initialization:** A BEE builder object will be intialized from a BEE builder class definition. The builder object will be instantiated with relevant beeconfig parameters and CWL parameters under the `DockerRequirement` specs. After a successfull initialization, a BEE builder getter will return a path to the configured container for a given workflow step.  
**Usage:** A BEE builder object will get the path to a container that meets the pre-conditions of the CWL `DockerRequirement` spec. A BEE builder object will also get the full list of parameters it was instantiated with.

## Container workloads
Each step in a workflow may include a reference to `DockerRequirement` in the CWL hints or requirements. If the `DockerRequirement` CWL hint is defined, any failure in the container runtime will result in a warning, and the workflow will attempt to run in the default baremetal environment. If the `DockerRequirement` CWL requirement is defined, any failure in the container runtime will result in an error and the workflow will terminate unsuccessfully. The `DockerRequirement` entry includes several fields:

1. `dockerPull:` Specify a container image to retrieve using the container runtime. This specifies the container name and tag. It does not include the path to the container. dockerPull should be used in combination with a container registery specified by dockerLoad, or a default will be assumed.
2. `dockerLoad:` The HTTP URL associated with the container registry in use. The container runtime requested will be specified by the `<container>://` prefix. dockerLoad must be used in combination with dockerPull, such that dockerPull defines what the required container image is named.
3. `dockerFile:` The path to a container definition file. The builder will fail if `dockerFile` is defined along with `dockerPull` or `dockerLoad`.
4. `dockerImport:` Provide HTTP URL to download and gunzip a Docker images using `docker import`. This should be the path to a compressed image. 
5. `dockerImageId:` A reference to the image id that will be invoked by the container runtime's `run` or `exec` command. Note that this differs from `dockerPull` slightly, in that `dockerPull` is the image to be acquired. It is possible to pull an image in a workflow stage, and then run an entirely different image by specifying a different `dockerImageId`. If `dockerImageId` is not defined, assume `dockerPull` references the container to run. If `dockerImageId` is specified and image does not exist, error.
6. `dockerOutputDirectory:` Set the designated output directory to a specific location inside the Docker container.
