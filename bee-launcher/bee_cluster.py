# system
import os
from subprocess import Popen, PIPE, \
    STDOUT, CalledProcessError
from threading import Thread, Event
from termcolor import cprint


class BeeTask(Thread):
    def __init__(self):
        Thread.__init__(self)

        # Output colors
        self.__output_color_list = ["magenta", "cyan", "blue", "green",
                                    "red", "grey", "yellow"]
        self.output_color = "cyan"
        self.error_color = "red"
        self.warning_color = "yellow"

        # Events for workflow
        self.__begin_event = Event()
        self.__end_event = Event()
        self.__event_list = []

    # Event/Trigger management
    @property
    def begin_event(self):
        return self.__begin_event

    @begin_event.setter
    def begin_event(self, flag):
        """
        If bool T then set internal flag,
        else clear internal flag
        :param flag: boolean value
        """
        if flag:
            self.__begin_event.set()
        else:
            self.__begin_event.clear()

    @property
    def end_event(self):
        return self.__end_event

    @end_event.setter
    def end_event(self, flag):
        """
        If bool T then set internal flag,
        else clear internal flag
        :param flag: boolean value
        """
        if flag:
            self.__end_event.set()
        else:
            self.__end_event.clear()

    @property
    def event_list(self):
        return self.__event_list

    @event_list.setter
    def event_list(self, new_event):
        """
        Append event to event_list
        :param new_event:
        """
        self.__event_list.append(new_event)

    # Task management support functions (public)
    def run_popen_safe(self, command, nodes=None, shell=False, err_exit=True):
        """
        Run defined command via Popen, try/except statements
        built in and message output when appropriate
        :param command: Command to be run
        :param nodes: Defaults to os.environ['SLURM_NODELIST']
                        Use to specify range of nodes message
                        applies too (pass string!)
        :param shell: Shell flag (boolean), default false
        :param err_exit: Exit upon error, default True
        """
        self.__handle_message("Executing: " + str(command), nodes)
        try:
            p = Popen(command, shell, stdout=PIPE, stderr=STDOUT)
            out, err = p.communicate()
            if out:
                self.__handle_message(msg=out, nodes=nodes)
            if err:
                self.__handle_message(msg=err, nodes=nodes,
                                      color=self.error_color)
        except CalledProcessError as e:
            self.__handle_message(msg="Error during - " + str(command) + "\n" +
                                  str(e), nodes=nodes, color=self.error_color)
            if err_exit:
                exit(1)
        except OSError as e:
            self.__handle_message(msg="Error during - " + str(command) + "\n" +
                                  str(e), nodes=nodes,  color=self.error_color)
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

    @staticmethod
    def compose_mpirun(command, hosts):
        # TODO: document
        srun_cmd = ["mpirun", "-host,", hosts, "--map-by", "ppr:1:node"]
        srun_cmd += command
        return srun_cmd

    # Task management support functions (private)
    @staticmethod
    def __handle_message(msg, nodes=None, color=None):
        """
        :param msg: To be printed to console
        :param nodes: Defaults to os.environ['SLURM_NODELIST']
                        Use to specify range of nodes message
                        applies too (pass string!)
        :param color: If message is be colored via termcolor
                        Default = none (normal print)
        """
        list_nodes = nodes
        if nodes is None:
            list_nodes = os.environ['SLURM_NODELIST']
        if color is None:
            print(list_nodes + " " + msg)
        else:
            cprint(list_nodes + " " + msg, color)