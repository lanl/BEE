"""Mid-level interface for managing a build system from WFM.

The WFM may request a Runtime Environment (RTE) that must be built.
This RTE build should be considered a separate stage in the workflow.
The build_interface will access components of the build_driver and
components of the gdb_interface as required.
"""

# from beeflow.common.gdb.gdb_interface import GraphDatabaseInterface
from beeflow.common.build.container_drivers import CharliecloudBuildDriver,
                                                   SingularityBuildDriver


class BuildInterfaceTM:
    """Interface for managing a build system with WFM.

    Requires an implemented subclass of BuildDriver (uses CharliecloudBuildDriver by default).
    """

    def __init__(self, bc):
        """Initialize the interface between tm and builder.

        :param bc: A BeeConfig object passed from Task Manager
        :type bc: beeflow.common.config.config_driver.BeeConfig
        """
        self.bc = bc
        # Get container type from BeeConfig
        try:
            container_type = bc.userconfig['builder'].get('container_type')
            # No container_type means builder needs more info to proceed.
            if not container_type:
                raise KeyError
        except KeyError:
            raise KeyError('BeeConfig [builder] lacks container_type. Did builder run here?')
        if container_type == 'charliecloud':
            self.build_driver = CharliecloudBuildDriver
        if container_type == 'SingularityBuildDriver':
            self.build_driver = SingularityBuildDriver
        else:
            raise NotImplementedError('{} is not implemented. Extend container_drivers.py'\
                                      .format(self.build_driver))

    def validate_environment(self):
