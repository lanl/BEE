#!/usr/bin/python
# system
import os
import sqlite3
from termcolor import cprint
# project
from .beefile_manager import BeefileLoader
from .launcher_translator import Adapter


class BeeLauncher(object):
    def __init__(self, log=False, log_dest="None"):
        # Logging configuration
        self.__log = log  # log flag (T/F)
        self.__log_dest = log_dest + ".launcher"  # log file destinations

        self.__cwdir = os.getcwd()
        self.__homedir = os.path.expanduser('~')

        # Database Tracking
        self._db_full = self.__homedir + "/.bee/launcher.db"
        self.__db_conn = None  # Database connection

        # Termcolor messages
        self._error_color = 'red'
        self._message_color = 'cyan'
        self._warning_color = 'yellow'

    def launch(self, beefile, task_name, file_loc):
        b_class = self._fetch_beefile_value(dictionary=beefile, key="class",
                                            quit_err=True)
        b_rjms = self._fetch_beefile_value(dictionary=beefile['requirements']['ResourceRequirement'],
                                           key="manageSys", quit_err=True)
        cprint("[" + str(task_name) + "] Preparing to launch..." +
               "\n\tClass: " + str(b_class) + "\n\tRJMS: " + str(b_rjms),
               self._message_color)
        adapt = Adapter(system=b_rjms, config=beefile, file_loc=file_loc,
                        task_name=task_name)
        out, err = adapt.allocate()

        if out is None:
            # Error during allocation phase
            pass
        else:  # Success
            pass

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

    ###########################################################################
    # Database reflated functions
    #
    ###########################################################################
    def __connect_db(self):
        self.__db_conn = sqlite3.connect(self._db_full)
        return self.__db_conn.cursor()

    def __close_db(self):
        self.__db_conn.close()

    def __launcher_table(self, cursor):
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS launcher "
                           "(tableID INTEGER PRIMARY KEY, "
                           "jobID TEXT NOT NULL, "
                           "class TEXT NOT NULL, "
                           "manageSys TEXT, "
                           "status TEXT, "
                           "beefileName TEXT, "
                           "beefileFull TEXT, "
                           "beeflowName TEXT, "
                           "beeflowFull TEXT, "
                           "errDetails TEXT, "
                           "time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL)")
        except sqlite3.Error as e:
            cprint("[" + self._db_full + "]Error while creating launcher table",
                   self._error_color)
            print(e)

    def __insert_launch_event(self):
        pass


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
