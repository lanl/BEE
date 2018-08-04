#!/usr/bin/python
# system
import os
# project
from beefile_manager import BeefileLoader


class BeeLauncher(object):
    def __init__(self, log, log_dest):
        # Logging configuration
        self.__log = log  # log flag (T/F)
        self.__log_dest = log_dest + ".launcher"  # log file destinations

        self.__cwdir = os.getcwd()

        self.__status_color = ['grey', 'white', 'yellow', 'cyan', 'green',
                               'magenta', 'red']
        self.__status = ["Initializing", "Initialized", "Waiting", "Launching",
                         "Running", "Finished", "Terminated"]

    def launch(self, beefile):
        pass

    def list_all_tasks(self):
        pass

    def terminate_task(self, beetask_name):
        pass

    def get_status_list(self):
        """
        :return: List of valid BeeLauncher status
        """
        return self.__status

    def get_status_color(self):
        """
        :return: List of valid BeeLauncher status colors
        """
        return self.__status_color

    def get_log_flag(self):
        """
        :return: Boolean, True if logging enabled
        """
        return self.__log

    def get_log_destination(self):
        """
        :return: File (path) where logging is stored
        """
        return self.__log_dest


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
        print("Sending launching request.")
        beefile_loader = BeefileLoader(beefile)
        beefile = beefile_loader.get_beefile()
        self.launch(beefile)

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
