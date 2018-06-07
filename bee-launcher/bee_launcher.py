#!/usr/bin/python
from __future__ import print_function
# system
import argparse
import getopt
import getpass
import json
import os
import Pyro4
import sys
import time
from tabulate import tabulate
from termcolor import colored, cprint
# project
from beefile_loader import BeefileLoader


class BeeLauncher(object):
    def __init__(self):
        self.__pydir = os.path.dirname(os.path.abspath(__file__))
        self.__cwdir = os.getcwd()
        self.__hdir = os.path.expanduser('~')
        f = open(self.__hdir + "/.bee/bee_conf.json", "r")
        data = json.load(f)
        port = int(data["pyro4-ns-port"])
        ns = Pyro4.locateNS(port=port, hmac_key=getpass.getuser())
        uri = ns.lookup("bee_launcher.daemon")
        self.bldaemon = Pyro4.Proxy(uri)  # Pyro4.Proxy("PYRONAME:bee_launcher.daemon")
        self.__status = ["Initializing", "Initialized", "Waiting", "Launching",
                         "Running", "Finished", "Terminated"]
        self.__status_color = ['grey', 'white', 'yellow', 'cyan', 'green',
                               'magenta', 'red']

    def launch(self, beefile, restore=False):
        self.encode_cwd(beefile)
        self.bldaemon.create_and_launch_task(beefile, restore)

    def list_all_tasks(self):
        return self.bldaemon.list_all_tasks()
        
    def checkpoint_task(self, beetask_name):
        return self.bldaemon.checkpoint_task(beetask_name)
    
    def terminate_task(self, beetask_name):
        self.bldaemon.terminate_task(beetask_name)

    def delete_task(self, beetask_name):
        self.bldaemon.delete_task(beetask_name)

    def create_bee_aws_storage(self, efs_name, perf_mode = 'generalPurpose'):
        return self.bldaemon.create_bee_aws_storage(efs_name, perf_mode)
    
    def encode_cwd(self, beefile):
        for run_conf in beefile['task_conf']['general_run']:
            run_conf['script'] = self.__cwdir + "/" + run_conf['script']
        for run_conf in beefile['task_conf']['mpi_run']:
            run_conf['script'] = self.__cwdir + "/"+ run_conf['script']

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


# Parser supporting functions
def verify_single_beefile(file):
    """
    Checks if file specified exists, if not errors and
    halts application
    :param file: argument provided by user (name)
    :return: argument IF .beefile found
    """
    tar = os.getcwd() + '/' + file + '.beefile'
    if os.path.isfile(tar):
        return file
    else:
        print(file + ".beefile cannot be found")
        exit(1)


parser = argparse.ArgumentParser(description="BEE Launcher")


# Launching/removing a task is currently only supported individually, thus
# they should remain mutually exclusive (launch_group)
launch_group = parser.add_mutually_exclusive_group()
launch_group.add_argument("-l", "--launch",
                          dest='launch_task', nargs=1,
                          type=verify_single_beefile,
                          help="Runs task specified by <LAUNCH_TASK>.beefile, "
                               "that needs to be in the current directory")
launch_group.add_argument("-r", "--restore",
                          dest='restore_task', nargs=1,
                          type=verify_single_beefile,
                          help="Restores task specified by <RESTORE_TASK>.beefile,"
                               " that needs to be in the current directory")
launch_group.add_argument("-c", "--checkpoint",
                          dest='checkpoint_task', nargs=1,
                          help="Checkpoint specified <CHECKPOINT_TASK>")
launch_group.add_argument("-t", "--terminate",
                          dest='terminate_task', nargs=1,
                          help="Terminate tasks <TERMINATE_TASK>")
launch_group.add_argument("-d", "--delete",
                          dest='delete_task', nargs=1,
                          help="Terminate and delete task <delete_task> from"
                               " the task list")
launch_group.add_argument("-e", "--efs",
                          dest='efs_name', nargs=1,
                          help="Create new efs with specified name <EFS_NAME>")

# Can be proceeding launch_group
# TODO: Can I force this to always be last?
parser.add_argument("-s", "--status",
                    action='store_true',
                    help="List all tasks with status, automatically "
                         "updates status")


def opt_launch(args, bee_launcher):
    """
    Send launch request for single task to daemon
    :param args: command line argument namespace
    :param bee_launcher: BeeLauncher() object
    :return: None
    """
    beefile = args.launch_task[0]
    print("Sending launching request.")
    beefile_loader = BeefileLoader(beefile)
    beefile = beefile_loader.get_beefile()
    bee_launcher.launch(beefile)


def opt_checkpoint(args, bee_launcher):
    """
    Send checkpoint request for single task to daemon
    :param args: command line argument namespace
    :param bee_launcher: BEELauncher() object
    :return: None
    """
    beetask_name = args.checkpoint_task[0]
    print("Sending checkpoint request.")
    bee_launcher.checkpoint_task(beetask_name)
    print("Task: " + beetask_name + " is checkpointed.")


def opt_restore(args, bee_launcher):
    """
    Send launch request for specified file to daemon,
    however restore from existing files
    :param args: command line argument namespace
    :param bee_launcher: BEELauncher() object
    :return: None
    """
    beefile = args.restore_task[0]
    print("Sending launching request.")
    beefile_loader = BeefileLoader(beefile)
    beefile = beefile_loader.get_beefile()
    bee_launcher.launch(beefile, True)


def opt_terminate(args, bee_launcher):
    """
    Send termination request for specific task to daemon
    :param args: command line argument namespace
    :param bee_launcher: BEELauncher() object
    :return: None
    """
    beetask_name = args.terminate_task[0]
    print("Sending termination request.")
    bee_launcher.terminate_task(beetask_name)
    print("Task: " + beetask_name + " is terminated.")


def opt_delete(args, bee_launcher):
    """
    Send delete request for specific task to daemon
    :param args: command line argument namespace
    :param bee_launcher: BEELauncher() object
    :return: None
    """
    beetask_name = args.delete_task[0]
    print("Sending deletion request.")
    bee_launcher.delete_task(beetask_name)
    print("Task: " + beetask_name + " is deleted.")


def opt_efs(args, bee_launcher):
    """
    Create new efs with specified name
    :param args: command line argument namespace
    :param bee_launcher: BEELauncher() object
    :return: None
    """
    arg = args.args.efs_name[0]
    efs_id = bee_launcher.create_bee_aws_storage(arg)
    if efs_id == "-1":
        print("EFS name already exists!")
    else:
        print("EFS created: " + efs_id)


def opt_status(bee_launcher):
    """

    :param bee_launcher:
    :return: None
    """
    while True:
        status = bee_launcher.list_all_tasks()
        if len(status) == 0:
            print("No task exist.")

        table = []
        count = 1
        for beetask in status:
            color_status = colored(bee_launcher.get_status_list()[status[beetask]['status']],
                                   bee_launcher.get_status_color()[status[beetask]['status']])
            platform = status[beetask]['platform']
            table.append([str(count), beetask, color_status, platform])
            count = count + 1
        os.system('clear')
        print(tabulate(table,
                       headers=['No.', 'Task Name', 'Status', 'Platform']))
        time.sleep(5)


def main():
    try:
        args = parser.parse_args()
        bee_launcher = BeeLauncher()

        if args.launch_task:
            opt_launch(args, bee_launcher)

        if args.restore_task:
            opt_restore(args, bee_launcher)

        if args.checkpoint_task:
            opt_checkpoint(args, bee_launcher)

        if args.terminate_task:
            opt_terminate(args, bee_launcher)

        if args.delete_task:
            opt_delete(args, bee_launcher)

        if args.efs_name:
            opt_efs(args, bee_launcher)

        if args.status:
            opt_status(bee_launcher)

    except argparse.ArgumentError, e:
        print(e.message)


if __name__ == "__main__":
    main()
