# system
from termcolor import cprint
# project
from bee_node import BeeNode


# TODO: implement run / root_run / parallel_run
# functions and operations focused on a single node
class BeeCharliecloud(BeeNode):
    def __init__(self, task_id, hostname, host, rank, task_conf, bee_cc_conf,
                 container_name):
        BeeNode.__init__(self, task_id=task_id, hostname=hostname, host=host,
                         rank=rank, task_conf=task_conf)

        # Charliecloud node configuration
        self.__bee_charliecloud_conf = bee_cc_conf
        self.__container_name = container_name

    def parallel_run(self, command, local_pfwd=None, remote_pfwd=None,
                     async=True):
        cmd = ["mpirun",
               "-host", self.__host,
               "--map-by", "ppr:1:node"]
        cmd += command
        self.run(command=cmd, local_pfwd=local_pfwd, remote_pfwd=remote_pfwd,
                 async=async)

    def unpack_image(self, container_path, ch_dir):
        # TODO: identify best method for async commands
        # Unpack image on each allocated node
        cprint("Unpacking container to {}".format(self.__host), self.__output_color)
        cmd = ['ch-tar2dir', container_path, ch_dir]
        try:
            self.parallel_run(command=cmd)
        except:  # TODO: drop except, move responsibility to run?
            cprint(" Error while unpacking image:", self.__error_color)


