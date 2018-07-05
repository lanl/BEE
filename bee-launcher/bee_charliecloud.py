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

        # TODO: re-address need with HOST()
        self.__node = host

        # Charliecloud node configuration
        self.__bee_charliecloud_conf = bee_cc_conf
        self.__container_name = container_name

    def parallel_run(self, command, local_pfwd=None, remote_pfwd=None,
                     async=True):
        print(BeeNode.hostname.__get__(self))
        cmd = ["mpirun",
               "-host", self.__node,
               "--map-by", "ppr:1:node"]
        cmd += command
        self.run(command=cmd, local_pfwd=local_pfwd, remote_pfwd=remote_pfwd,
                 async=async)

    def unpack_image(self, container_path, ch_dir):
        # Unpack image on each allocated node
        cprint("[" + self.__node + "]Unpacking container to {}".format(ch_dir), self.output_color)
        cmd = ['ch-tar2dir', str(container_path), ch_dir]
        try:
            self.parallel_run(command=cmd)
        except:  # TODO: drop except, move responsibility to run?
            cprint(" Error while unpacking image:", self.error_color)
