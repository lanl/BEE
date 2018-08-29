# system
from subprocess import Popen, PIPE, \
    STDOUT, CalledProcessError
from termcolor import cprint


class BeeNode(object):
    def __init__(self, task_id, hostname, host, rank, task_conf,
                 shared_dir=None, user_name="beeuser"):
        # Basic configurations
        self.__status = ""
        self.__hostname = hostname
        self.rank = rank
        self.master = ""
        self._node = host

        # Job configuration
        self.task_id = task_id
        self.task_conf = task_conf

        # Shared resourced
        self.shared_dir = shared_dir
        self.user_name = user_name

        # Output color list
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
        self.run_popen_safe(command=cmd)

    @property
    def status(self):
        return self.__status

    @status.setter
    def status(self, status):
        cprint("[" + self.__hostname + "]: Setting status", self.output_color)
        self.__status = status

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
                self._handle_message(msg=out)
            if err:
                self._handle_message(msg=err, color=self.error_color)
        except CalledProcessError as e:
            self._handle_message(msg="Error during - " + str(command) + "\n" +
                                 str(e), color=self.error_color)
            if err_exit:
                exit(1)
        except OSError as e:
            self._handle_message(msg="Error during - " + str(command) + "\n" +
                                 str(e),  color=self.error_color)
            if err_exit:
                exit(1)

    def _handle_message(self, msg, color=None):
        """
        :param msg: To be printed to console
        :param color: If message is be colored via termcolor
                        Default = none (normal print)
        """
        if color is None:
            print("[" + self._node + "] " + msg)
        else:
            cprint("[" + self._node + "] " + msg, color)
