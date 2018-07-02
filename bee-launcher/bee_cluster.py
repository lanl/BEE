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
    def run_popen_safe(self, command, nodes=None, shell=False):
        """
        Run defined command via Popen, try/except statements
        built in and message output when appropriate
        :param command: Command to be run
        :param nodes: Defaults to os.environ['SLURM_NODELIST']
                        Use to specify range of nodes message
                        applies too (pass string!)
        :param shell: Shell flag (boolean), default false
        :return:
        """
        try:
            p = Popen(command, shell, stdout=PIPE, stderr=STDOUT)
            out, err = p.communicate()
            if out:
                print()
                self.__handle_message(msg=out, nodes=nodes)
            if err:
                self.__handle_message(msg=err, nodes=nodes,
                                      color=self.error_color)
        except CalledProcessError as e:
            self.__handle_message(msg="Error during - " + str(command) + "\n" +
                                  str(e), nodes=nodes, color=self.error_color)
        except OSError as e:
            self.__handle_message(msg="Error during - " + str(command) + "\n" +
                                  str(e), nodes=nodes,  color=self.error_color)

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