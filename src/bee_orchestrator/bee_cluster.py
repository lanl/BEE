# system
import os
from subprocess import Popen, PIPE, \
    STDOUT, CalledProcessError
from threading import Thread, Event
from termcolor import cprint
from pwd import getpwuid
# project
from translator import Adapter


class BeeTask(Thread):
    def __init__(self, task_id, beefile):
        Thread.__init__(self)

        # Task configuration
        self.platform = None
        self._beefile = beefile
        self._task_id = task_id
        self._task_label = self._beefile.get('label', 'BEE-Charliecloud: {}'.
                                             format(self._task_id))

        # System configuration
        self._user_name = getpwuid(os.getuid())[0]
        self._rjms = self._beefile['requirements']['ResourceRequirement']\
            .get('rjms', 'ssh')
        self._sys_adapter = Adapter(system=self._rjms, config=self._beefile,
                                    file_loc='', task_name=self._task_id)

        # Output colors
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
        self._handle_message("Executing: " + str(command), nodes)
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
                                 str(e), color=self.error_color)
            if err_exit:
                exit(1)

    # Task management support functions (private)
    def _handle_message(self, msg, color=None):
        """
        :param msg: To be printed to console
        :param color: If message is be colored via termcolor
                        Default = none (normal print)
        """

        if color is None:
            print("[{}] {}".format(self._task_id, msg))
        else:
            cprint("[{}] {}".format(self._task_id, msg), color)
