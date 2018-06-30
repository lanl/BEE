# system
import subprocess
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

    def unpack_image(self, container_path, ch_dir):
        # TODO: identify best method for async commands
        # Unpack image on each allocated node
        cprint("Unpacking container to {}".format(self.__host), self.__output_color)
        cmd = ['mpirun', '-host', self.__host, '--map-by', 'ppr:1:node',
               'ch-tar2dir', container_path, ch_dir]

        try:
            subprocess.call(cmd)
        except:
            cprint(" Error while unpacking image:", self.__error_color)