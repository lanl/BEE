"""Abstract base class for the handling build systems."""

from abc import ABC, abstractmethod
import jsonpickle


def arg2task(task_arg):
    """Convert JSON encoded task to Task object.

    The build driver will expect a Task object, and the build
    interface starts with a JSON representation of the Task object.
    """
    return jsonpickle.decode(task_arg)


def task2arg(task):
    """Convert Task object to JSON encoded string.

    The build interface needs to pass Task data on the command line,
    because each compute node needs to understand the Task description.
    JSON format is a convenient way to describe the Task object at the
    command line.
    """
    return jsonpickle.encode(task)


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
    def process_docker_pull(self, addr, force):
        """Get and process the CWL compliant dockerPull dockerRequirement.

        CWL spec 09-23-2020: Specify a Docker image to
        retrieve using docker pull. Can contain the immutable
        digest to ensure an exact container is used.
        """

    @abstractmethod
    def process_docker_load(self):
        """Get and process the CWL compliant dockerLoad dockerRequirement.

        CWL spec 09-23-2020: Specify a HTTP URL from which to
        download a Docker image using docker load.
        """

    @abstractmethod
    def process_docker_file(self, task_dockerfile, force):
        """Get and process the CWL compliant dockerFile dockerRequirement.

        CWL spec 09-23-2020: Supply the contents of a Dockerfile
        which will be built using docker build.
        """

    @abstractmethod
    def process_docker_import(self, param_import):
        """Get and process the CWL compliant dockerImport dockerRequirement.

        CWL spec 09-23-2020: Provide HTTP URL to download and
        gunzip a Docker images using docker import.
        """

    @abstractmethod
    def process_docker_image_id(self, param_imageid):
        """Get and process the CWL compliant dockerImageId dockerRequirement.

        CWL spec 09-23-2020: The image id that will be used for
        docker run. May be a human-readable image name or the
        image identifier hash. May be skipped if dockerPull is
        specified, in which case the dockerPull image id must be
        used.
        """

    @abstractmethod
    def process_docker_output_directory(self, param_output_directory):
        """Get and process the CWL compliant dockerOutputDirectory dockerRequirement.

        CWL spec 09-23-2020: Set the designated output directory
        to a specific location inside the Docker container.
        """

    @abstractmethod
    def process_copy_container(self, force):
        """Get and process the BEE CWL extension copyContainer dockerRequirement.

        This CWL extension will copy an existing container to the build archive.

        If you have a container tarball, and all you need to do is stage it,
        that is, all you need to do is copy it to a location that BEE knows,
        use this to put the container into the build archive.
        """

    @abstractmethod
    def process_container_name(self):
        """Get and process BEE CWL extension for containerName dockerRequirement.

        This is a BEE extension to CWL to refer to containers with human-readable name.

        The CWL spec currently uses dockerImageId to refer to the name of a container
        but this is explicitly not how Docker defines it. We need a way to name
        containers in a human readable format.
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
        # (bound method, method name, priority, terminal case bool)
        cwl_spec = [(self.process_docker_pull, 'dockerPull', 5, True),
                    (self.process_docker_load, 'dockerLoad', 6, True),
                    (self.process_docker_file, 'dockerFile', 7, True),
                    (self.process_docker_import, 'dockerImport', 4, True),
                    (self.process_copy_container, 'beeflow:copyContainer', 3, True),
                    (self.process_docker_image_id, 'dockerImageId', 1, False),
                    (self.process_container_name, 'beeflow:containerName', 2, False),
                    (self.process_docker_output_directory, 'dockerOutputDirectory', 0, False)]
        exec_list = sorted(cwl_spec, key=lambda x: x[2])
        return exec_list
