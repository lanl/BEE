"""Abstract base class for the handling build systems."""

from abc import ABC, abstractmethod


class BuildDriver(ABC):
    """Driver interface between WFM and a generic build system.

    A driver object must implement an __init__ method that
    requests a Runtime Environment (RTE), and a method to 
    return the requested RTE.
    """

    @abstractmethod
    def initialize_builder(self, requirements, hints, kwargs):
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
