# system
import os
from termcolor import cprint
# project
from host import Host


class BeeNode(object):
    def __init__(self, task_id, hostname, host, rank, task_conf,
                 shared_dir=None, user_name="beeuser"):
        # Basic configurations
        self.__status = ""
        self.__hostname = hostname
        self.__rank = rank
        self.__master = ""

        # Job configuration
        self.__task_id = task_id
        self.__task_conf = task_conf

        # Host machine
        self.__host = Host(host)

        # Shared resourced
        self.__shared_dir = shared_dir
        self.__user_name = user_name

        # Output color list
        self.__output_color_list = ["magenta", "cyan", "blue", "green",
                                    "red", "grey", "yellow"]
        self.__output_color = "cyan"
        self.__error_color = "red"

    # Accessors
    def get_hostname(self):
        return self.__hostname

    def get_status(self):
        return self.__status

    def get_master(self):
        return self.__master

    def get_shared_dir(self):
        return self.__shared_dir

    def get_user_name(self):
        return self.__user_name

    # Modifiers
    def set_hostname(self):
        cprint("[" + self.__hostname + "]: set hostname.", self.__output_color)
        cmd = ["hostname",
               self.__hostname]
        self.root_run(cmd)

    def set_status(self, status):
        cprint("[" + self.__hostname + "]Setting status", self.__output_color)
        self.__status = status

    def set_master(self, master):
        self.__master = master

    # Run / CLI related functions
    def run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        # TODO: document
        return self.__host.run(command=command, local_pfwd=local_pfwd,
                               remote_pfwd=remote_pfwd, async=async)

    def root_run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        # TODO: docucment
        return self.__host.run(command=command, local_pfwd=local_pfwd,
                               remote_pfwd=remote_pfwd, async=async)

    def parallel_run(self, command, local_pfwd=None, remote_pfwd=None, async=False):
        pass

    # Directory / storage support functions
    def create_shared_dir(self):
        # Create directory
        # TODO: implement checks
        cprint("[" + self.__hostname + "]: create shared directory.",
               self.__output_color)
        cmd = ["mkdir",
               "{}".format(self.__shared_dir)]
        self.root_run(cmd)

    def update_ownership(self):
        # TODO: implement checks
        cprint("[" + self.__hostname + "]: update ownership of shared directory.",
               self.__output_color)
        cmd = ["chown",
               "-R",
               "{}:{}".format(self.__user_name, self.__user_name),
               "{}".format(self.__shared_dir)]
        self.root_run(cmd)

    def update_uid(self):
        cprint("[" + self.__hostname + "]: update user UID.", self.__output_color)
        # Change user's UID to match host's UID.
        # This is necessary for dir sharing.
        cmd = ["usermod",
               "-u {} {}".format(os.getuid(), self.__user_name)]

        self.root_run(cmd)

    def update_gid(self):
        cprint("[" + self.__hostname + "]: update user GID.", self.__output_color)
        # Change user's GID to match host's GID.
        # This is necessary for dir sharing.
        cmd = ["groupmod",
               "-g {} {}".format(os.getgid(), self.__user_name)]

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
