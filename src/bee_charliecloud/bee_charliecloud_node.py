# system
from termcolor import cprint
from subprocess import Popen
# project
from bee_node import BeeNode


# functions and operations focused on a single node
class BeeCharliecloud(BeeNode):
    def __init__(self, task_id, hostname, host, rank, task_conf, bee_cc_conf,
                 container_name):
        BeeNode.__init__(self, task_id=task_id, hostname=hostname, host=host,
                         rank=rank, task_conf=task_conf)

        # Node currently running on (for ease of use)
        self.__node = host

        # Charliecloud node configuration
        self.__bee_charliecloud_conf = bee_cc_conf
        self.__container_name = container_name

    def general_run(self, script_path, local_pfwd=None, remote_pfwd=None):
        """
        Override base general_run in order to implement module work around.
        Load Charliecloud prior to running the script...
        """
        cmd = ['sh', script_path]
        cprint("[" + self.__node + "] general run: " + str(cmd),
               self.output_color)
        self.run_popen_safe(cmd)

    # MPI supporting functions
    def mpi_parallel_run(self, command, async=False):
        """
        Using mpirun
        Run command via mpirun on this node (self.__node)
        NOTE: local_pfwd & remote_pfwd are not utilized
        Use async to run command without try/except
        """
        print(BeeNode.hostname.__get__(self))
        cmd = self.__prepare_mpirun(command)
        if async:
            Popen(cmd)
        else:
            self.run_popen_safe(cmd)

    def mpi_unpack_image(self, container_path, ch_dir):
        """
        Using mpirun
        Unpack image via ch-tar2dir on a single node
        ch-tar2dir container_path ch_dir
        """
        cprint("[" + self.__node + "]Unpacking container to {}".format(ch_dir),
               self.output_color)
        cmd = ['ch-tar2dir', str(container_path), ch_dir]
        self.run_popen_safe(cmd)

    # Task management support functions (private)
    def __prepare_mpirun(self, command):
        """
        :param command: Linux command, list formant
        :return: List, mpirun command to be run via subprocess
        """
        cmd = ["mpirun",
               "-host", self.__node,
               "--map-by", "ppr:1:node"]
        cmd += command
        return cmd
