# system
from termcolor import cprint
from subprocess import Popen
# project
from bee_node import BeeNode


# functions and operations focused on a single node
class BeeCharliecloudNode(BeeNode):
    def __init__(self, task_id, hostname, host, rank, task_conf,
                 container_name):
        BeeNode.__init__(self, task_id=task_id, hostname=hostname, host=host,
                         rank=rank, task_conf=task_conf)

        # Node currently running on (for ease of use)
        self.__node = host

        # Charliecloud node configuration
        self.__container_name = container_name

    def general_run(self, script_path):
        """
        Override base general_run in order to implement module work around.
        Load Charliecloud prior to running the script...
        """
        cmd = ['sh', script_path]
        cprint("[" + self.__node + "] general run: " + str(cmd),
               self.output_color)
        self.run_popen_safe(cmd)
