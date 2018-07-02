# system
from termcolor import cprint
from subprocess import Popen, PIPE, \
    STDOUT, CalledProcessError
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
            self.__run_popen_safe(cmd)

    def unpack_image(self, container_path, ch_dir):
        """
        Unpack image via ch-tar2dir on a single node
        ch-tar2dir container_path ch_dir
        """
        cprint("[" + self.__node + "]Unpacking container to {}".format(ch_dir),
               self.output_color)
        cmd = ['ch-tar2dir', str(container_path), ch_dir]
        self.__run_popen_safe(cmd)

    # Support functions
    def __run_popen_safe(self, command, shell=False):
        """
        Run defined command via Popen, try/except statements
        built in and message output when appropriate
        :param command: Command to be run
        :param shell: Shell flag (boolean), default false
        :return:
        """
        try:
            p = Popen(command, shell, stdout=PIPE, stderr=STDOUT)
            out, err = p.communicate()
            if out:
                print()
                self.__handle_message(msg=out)
            if err:
                self.__handle_message(msg=err, color=self.error_color)
        except CalledProcessError as e:
            self.__handle_message(msg="Error during - " + str(command) + "\n" +
                                  str(e), color=self.error_color)
        except OSError as e:
            self.__handle_message(msg="Error during - " + str(command) + "\n" +
                                  str(e), color=self.error_color)

    def __handle_message(self, msg, color=None):
        """
        :param msg: To be printed to console
        :param color: If message is be colored via termcolor
                        Default = none (normal print)
        """
        if color is None:
            print("[" + self.__node + "] " + msg)
        else:
            cprint("[" + self.__node + "] " + msg, color)
