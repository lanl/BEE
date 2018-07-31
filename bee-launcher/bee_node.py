# system
import os
from subprocess import Popen, PIPE, \
    STDOUT, CalledProcessError
from termcolor import cprint
# project
from host import Host


class BeeNode(object):
    def __init__(self, task_id, hostname, host, rank, task_conf,
                 shared_dir=None, user_name="beeuser"):
        # Basic configurations
        self.__status = ""
        self.__hostname = hostname
        self.rank = rank
        self.master = ""

        # Job configuration
        self.task_id = task_id
        self.task_conf = task_conf

        # Host machine
        self.__node = host
        self.host = Host(host)

        # Shared resourced
        self.shared_dir = shared_dir
        self.user_name = user_name

        # Output color list
        self.__output_color_list = ["magenta", "cyan", "blue", "green",
                                    "red", "grey", "yellow"]
        self.output_color = "cyan"
        self.error_color = "red"

    @property
    def hostname(self):
        return self.__hostname

    @hostname.setter
    def hostname(self, h):
        cprint("[" + self.__hostname + "]: setting hostname to " + h,
               self.output_color)
        cmd = ["hostname", self.__hostname]
        self.root_run(cmd)

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status):
        cprint("[" + self.__hostname + "]: Setting status", self.output_color)
        self.__status = status

    # Run / CLI related functions
    def run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        if local_pfwd is None:
            local_pfwd = []
        if remote_pfwd is None:
            remote_pfwd = []
        return self.host.run(command=command, local_pfwd=local_pfwd,
                             remote_pfwd=remote_pfwd, async=async)

    def root_run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        if local_pfwd is None:
            local_pfwd = []
        if remote_pfwd is None:
            remote_pfwd = []
        return self.host.run(command=command, local_pfwd=local_pfwd,
                             remote_pfwd=remote_pfwd, async=async)

    def parallel_run(self, command, local_pfwd=None, remote_pfwd=None,
                     async=True):
        self.run(command=command, local_pfwd=local_pfwd,
                 remote_pfwd=remote_pfwd, async=async)

    # Task configuration run mode
    def general_run(self, script_path, local_pfwd=None, remote_pfwd=None):
        cmd = ['sh', script_path]
        cprint("[" + self.__hostname + "] general run: " + str(cmd),
               self.output_color)
        self.run(cmd, local_pfwd, remote_pfwd)

    # Directory / storage support functions
    def create_shared_dir(self):
        # Create directory
        cprint("[" + self.__hostname + "]: create shared directory.",
               self.output_color)
        cmd = ["mkdir",
               "{}".format(self.shared_dir)]
        self.root_run(cmd)

    def update_ownership(self):
        cprint("[" + self.__hostname + "]: update ownership of shared directory.",
               self.output_color)
        cmd = ["chown",
               "-R",
               "{}:{}".format(self.user_name, self.user_name),
               "{}".format(self.shared_dir)]
        self.root_run(cmd)

    def update_uid(self):
        cprint("[" + self.__hostname + "]: update user UID.", self.output_color)
        # Change user's UID to match host's UID.
        # This is necessary for dir sharing.
        cmd = ["usermod",
               "-u {} {}".format(os.getuid(), self.user_name)]

        self.root_run(cmd)

    def update_gid(self):
        cprint("[" + self.__hostname + "]: update user GID.", self.output_color)
        # Change user's GID to match host's GID.
        # This is necessary for dir sharing.
        cmd = ["groupmod",
               "-g {} {}".format(os.getgid(), self.user_name)]

        self.root_run(cmd)

    # Bee launching / management related functions
    def start(self):
        pass

    def checkpoint(self):
        pass

    def restore(self):
        pass

    def kill(self):
        pass

    # Task management support functions (private)
    def run_popen_safe(self, command, shell=False, err_exit=True):
        """
        Run defined command via Popen, try/except statements
        built in and message output when appropriate
        :param command: Command to be run
        :param shell: Shell flag (boolean), default false
        :param err_exit: Exit upon error, default True
        """
        try:
            p = Popen(command, shell, stdout=PIPE, stderr=STDOUT)
            out, err = p.communicate()
            if out:
                self.__handle_message(msg=out)
            if err:
                self.__handle_message(msg=err, color=self.error_color)
        except CalledProcessError as e:
            self.__handle_message(msg="Error during - " + str(command) + "\n" +
                                  str(e), color=self.error_color)
            if err_exit:
                exit(1)
        except OSError as e:
            self.__handle_message(msg="Error during - " + str(command) + "\n" +
                                  str(e),  color=self.error_color)
            if err_exit:
                exit(1)

    @staticmethod
    def compose_srun(command, hosts=None, num_nodes=None):
        """
        Compose SRUN command to be run via subprocess
        https://slurm.schedmd.com/srun.html
        e.g. - srun --nodelist=cn30,cn31 --nodes=2-2 <command>
        :param command: Command to be run [List]
        :param hosts: Specific hosts (nodes) command is to be run on (str)
        :param num_nodes: Min/Max number of nodes allocated to job
        :return: [List] to be run via subprocess
        """
        srun_cmd = ["srun"]
        if hosts is not None:
            srun_cmd += ["--nodelist=" + hosts]
        if num_nodes is not None:
            srun_cmd += ["--nodes=" + str(num_nodes) + "-" + str(num_nodes)]
        srun_cmd += command
        return srun_cmd

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
