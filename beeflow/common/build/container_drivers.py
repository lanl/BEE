"""Container build driver.

All container-based build systems belong here.
"""

from abc import ABC
# from beeflow.common.crt.crt_drivers import CharliecloudDriver, SingularityDriver


class ContainerBuildDriver(ABC):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """


class CharliecloudBuildDriver(ContainerBuildDriver):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """

    def initialize_builder(self, requirements, hints, bc_options):
        """Begin build request.

        Parse hints and requirements to determine target build
        system. Harvest relevant BeeConfig params in bc_options.

        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        :param bc_options: Dictionary of build system config options
        :type bc_options: set of build system parameters
        """
        print('Charliecloud, initialize_builder:', self, requirements, hints, bc_options, '.')

    def parse_build_config(self):
        """Parse bc_options to separate BeeConfig and CWL concerns.

        bc_options is used to receive an unknown number of parameters.
        both BeeConfig and CWL files may have options required for
        the build service. Parse and store them.
        """
        print('Charliecloud, parse_build_config:', self, '.')

    def validate_build_config(self):
        """Ensure valid config.

        Parse bc_options to ensure BeeConfig options are compatible
        with CWL specs.
        """
        print('Charliecloud, validate_build_config:', self, '.')

    def build(self):
        """Build RTE as configured.

        Build the RTE based on a validated configuration.
        """
        print('Charliecloud, validate_build_config:', self, '.')

    def validate_build(self):
        """Validate RTE.

        Confirm build procedure completed successfully.
        """
        print('Charliecloud, validate_build:', self, '.')


class SingularityBuildDriver(ContainerBuildDriver):
    """Driver interface between WFM and a container build system.

    A driver object must implement an __init__ method that
    requests a RTE, and a method to return the requested RTE.
    """

    def initialize_builder(self, requirements, hints, bc_options):
        """Begin build request.

        Parse hints and requirements to determine target build
        system. Harvest relevant BeeConfig params in bc_options.

        :param requirements: the workflow requirements
        :type requirements: set of Requirement instances
        :param hints: the workflow hints (optional requirements)
        :type hints: set of Requirement instances
        :param bc_options: Dictionary of build system config options
        :type bc_options: set of build system parameters
        """
        print('Singularity, initialize_builder:', self, requirements, hints, bc_options, '.')

    def parse_build_config(self):
        """Parse bc_options to separate BeeConfig and CWL concerns.

        bc_options is used to receive an unknown number of parameters.
        both BeeConfig and CWL files may have options required for
        the build service. Parse and store them.
        """
        print('Singularity, parse_build_config:', self, '.')

    def validate_build_config(self):
        """Ensure valid config.

        Parse bc_options to ensure BeeConfig options are compatible
        with CWL specs.
        """
        print('Singularity, validate_build_config:', self, '.')

    def build(self):
        """Build RTE as configured.

        Build the RTE based on a validated configuration.
        """
        print('Singularity, validate_build_config:', self, '.')

    def validate_build(self):
        """Validate RTE.

        Confirm build procedure completed successfully.
        """
        print('Singularity, validate_build:', self, '.')
