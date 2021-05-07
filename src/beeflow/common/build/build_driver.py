"""Abstract base class for the handling build systems."""

from abc import ABC, abstractmethod
from beeflow.common.wf_data import BuildTask
import json

def arg2task(task_arg):
    task_arg = dict(json.loads(task_arg))
    task = BuildTask(name=task_arg['name'],
                    command=task_arg['command'],
                    requirements=task_arg['requirements'],
                    hints=task_arg['hints'],
                    subworkflow=task_arg['subworkflow'],
                    inputs=task_arg['inputs'],
                    outputs=task_arg['outputs'])
    return(task)

task2arg = lambda task: json.dumps(vars(task))

class BuildDriver(ABC):
    """Driver interface between WFM and a generic build system.

    A driver object must implement an __init__ method that
    requests a Runtime Environment (RTE), and a method to
    return the requested RTE.
    """

    @abstractmethod
    def __init__(self, task, kwargs):
        """Begin build request.

        Parse hints and requirements to determine target build
        system. Harvest relevant BeeConfig params in kwargs.

        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        :param kwargs: Dictionary of build system config options
        :type kwargs: set of build system parameters
        """

    @abstractmethod
    def dockerPull(self, addr):
        """CWL compliant dockerPull.

        CWL spec 09-23-2020: Specify a Docker image to
        retrieve using docker pull. Can contain the immutable
        digest to ensure an exact container is used.
        """

    @abstractmethod
    def dockerLoad(self):
        """CWL compliant dockerLoad.

        CWL spec 09-23-2020: Specify a HTTP URL from which to
        download a Docker image using docker load.
        """

    @abstractmethod
    def dockerFile(self):
        """CWL compliant dockerFile.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build.
        """

    @abstractmethod
    def dockerImport(self):
        """CWL compliant dockerImport.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import.
        """

    @abstractmethod
    def dockerImageId(self):
        """CWL compliant dockerImageId.

        CWL spec 09-23-2020: The image id that will be used for
        docker run. May be a human-readable image name or the
        image identifier hash. May be skipped if dockerPull is
        specified, in which case the dockerPull image id must be
        used.
        """

    @abstractmethod
    def dockerOutputDirectory(self):
        """CWL compliant dockerOutputDirectory.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container.
        """

    def resolve_priority(self):
        """Given multiple DockerRequirements, set order of execution.

        The CWL spec as of 04-15-2021 does not specify order of
        execution, but the cwltool gives some guidance by example.
        We mimic cwltool in how we resolve priority, favoring
        fast, cached container specs over slower specs. For example,
        if both a docker pull and a docker file are supported, the
        build interface will try to pull first, and only on pull
        failure will the builder build the docker file. 
        """
        # cwl spec priority list consists of:
        # (bound method, method name, priority, termainal case bool)
        cwl_spec = [(self.dockerPull,'dockerPull',3, True),
                    (self.dockerLoad,'dockerLoad',4, True),
                    (self.dockerFile,'dockerFile',5, True),
                    (self.dockerImport,'dockerImport',2, True),
                    (self.dockerImageId,'dockerImageId',1, False),
                    (self.dockerOutputDirectory,'dockerOutputDirectory',0, False)
                   ]
        exec_list = sorted(cwl_spec, key=lambda x:x[2])
        return(exec_list)
# Ignore snake_case requirement to enable CWL compliant names.
# pylama:ignore=C0103
