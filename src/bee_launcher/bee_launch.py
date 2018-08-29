#!/usr/bin/python
# system
import os
from termcolor import cprint
# project
from beefile_manager import BeefileLoader
from launcher_translator import Adapter


class BeeLauncher(object):
    def __init__(self, log=False, log_dest="None"):
        # Logging configuration
        self.__log = log  # log flag (T/F)
        self.__log_dest = log_dest + ".launcher"  # log file destinations

        self.__cwdir = os.getcwd()

        self._status_color = ['grey', 'white', 'yellow', 'cyan', 'green',
                            'magenta', 'red']
        self._error_color = 'red'
        self._message_color = 'cyan'
        self._warning_color = 'yellow'
        self._status = ["Initializing", "Initialized", "Waiting", "Launching",
                        "Running", "Finished", "Terminated"]

    def launch(self, beefile, task_name, file_loc):
        b_class = self._fetch_beefile_value(dictionary=beefile, key="class",
                                            quit_err=True)
        b_rjms = self._fetch_beefile_value(dictionary=beefile['requirements']['ResourceRequirement'],
                                           key="rjms", quit_err=True)
        cprint("[" + str(task_name) + "] Preparing to launch..." +
               "\n\tClass: " + str(b_class) + "\n\tRJMS: " + str(b_rjms),
               self._message_color)
        adapt = Adapter(system=b_rjms, config=beefile, file_loc=file_loc,
                        task_name=task_name)
        adapt.allocate()

    def list_all_tasks(self):
        # TODO: implement
        pass

    def terminate_task(self, beetask_name):
        # TODO: implement
        pass

    @property
    def log_flag(self):
        """
        :return: Boolean, True if logging enabled
        """
        return self.__log

    @property
    def log_dest(self):
        """
        :return: File (path) where logging is stored
        """
        return self.__log_dest

    def _fetch_beefile_value(self, dictionary, key, default=None,
                             quit_err=False, silent=False):
        try:
            return dictionary[key]
        except KeyError:
            if default is not None and not quit_err:
                if not silent:
                    cprint("User defined value for ["
                           + str(key) + "] was not found, default value: "
                           + str(default) + " used.", self._warning_color)
                return default
            else:
                cprint("Key: " + str(key) + " was not found",
                       self._error_color)
            exit(1)


# Manage main argument responses
class BeeArguments(BeeLauncher):
    def __init__(self, log=False, log_dest='/var/tmp/bee.log'):
        BeeLauncher.__init__(self, log, log_dest)

    def opt_launch(self, args):
        """
        Send launch request for single task to daemon
        :param args: command line argument namespace
        :return: None
        """
        beefile = str(args.launch_task[0])
        f = BeefileLoader(beefile)
        self.launch(beefile=f.beefile, task_name=beefile,
                    file_loc=os.path.dirname(os.path.abspath("{}.beefile".format
                                                             (beefile))))

    def opt_terminate(self, args):
        """
        Send termination request for specific task to daemon
        :param args: command line argument namespace
        :return: None
        """
        beetask_name = args.terminate_task[0]
        print("Sending termination request.")
        self.terminate_task(beetask_name)
        print("Task: " + beetask_name + " is terminated.")

    # TODO: implement high level status support using job id
    def opt_status(self):
        pass
