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

    # Override the parent in order to support running with Host class
    def run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        if local_pfwd is not None or remote_pfwd is not None:
            # TODO: review and possibly implement
            # The Charliecloud launcher at this moment does not support the
            # port forwarding functionality found in other modules. This
            # should be discussed further before implementing
            cprint("Error: port-forwarding via run is not support, please contact "
                   "the developer", self.error_color)
            if async:
                Popen(command)
            else:
                self.run_popen_safe(command)

    def parallel_run(self, command, local_pfwd=None, remote_pfwd=None,
                     async=False):
        """
        Run command via mpirun on this node (self.__node)
        NOTE: local_pfwd & remote_pfwd are not utilized
        Use async to run command without try/except
        """
        print(BeeNode.hostname.__get__(self))
        cmd = ["mpirun",
               "-host", self.__node,
               "--map-by", "ppr:1:node"]
        cmd += command
        if async:
            # TODO: investigate alternative methods
            Popen(cmd)
        else:
            self.run_popen_safe(cmd)

    def unpack_image(self, container_path, ch_dir):
        """
        Unpack image via ch-tar2dir on a single node
        ch-tar2dir container_path ch_dir
        """
        cprint("[" + self.__node + "]Unpacking container to {}".format(ch_dir),
               self.output_color)
        cmd = ['ch-tar2dir', str(container_path), ch_dir]
        self.run_popen_safe(cmd)
