"""Abstract base class for the handling build systems."""

from abc import ABC, abstractmethod


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
    def parse_build_config(self):
        """Parse kwargs to separate BeeConfig and CWL concerns.

        kwargs is used to receive an unknown number of parameters.
        both BeeConfig and CWL files may have options required for
        the build service. Parse and store them.
        """

    @abstractmethod
    def validate_build_config(self):
        """Ensure valid config.

        Parse kwargs to ensure BeeConfig options are compatible
        with CWL specs.
        """

    @abstractmethod
    def build(self):
        """Build RTE as configured.

        Build the RTE based on a validated configuration.
        """

    @abstractmethod
    def validate_build(self):
        """Validate RTE.

        Confirm build procedure completed successfully.
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
# Ignore snake_case requirement to enable CWL compliant names.
# pylama:ignore=C0103
