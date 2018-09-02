# system
import argparse
import sys
from os import getcwd, path
from termcolor import cprint
# project
from .bee_launch import BeeArguments
from .bee_flow import BeeFlow


# Parser supporting functions
def verify_single_beefile(potential_file):
    """
    Checks if file specified exists, if not errors and
    halts application
    :param potential_file: argument provided by user (name)
    :return: argument IF .beefile found
    """
    tar = getcwd() + '/' + potential_file + '.beefile'
    if path.isfile(tar):
        return potential_file
    else:
        cprint(potential_file + ".beefile cannot be found", "red")
        exit(2)


def verify_single_beeflow(potential_file):
    """
    Checks if file specified exists, if not errors and
    halts application
    :param potential_file: argument provided by user (name)
    :return: argument IF .beeflow found
    """
    tar = getcwd() + "/" + potential_file + '.beeflow'
    if path.isfile(tar):
        return potential_file
    else:
        print(potential_file + ".beeflow cannot be found")
        exit(2)


###############################################################################
# Default arg functions, responsible for identifying and acting upon arguments
# from specified sub-parsers
# package --arg subparser --subarg task_name
# Example: bee --logflag launch -l
#
# See Python official documentation:
# https://docs.python.org/2.7/library/argparse.html
###############################################################################
def launch_default(args):
    bee_args = None
    try:
        bee_args = BeeArguments(args.logflag, args.log_dest)
    except Exception as e:
        print(e)
        cprint("Verify Bee Orchestrator is running!", "red")
        exit(2)

    # execute task if argument is present
    # exclusivity rules are managed by argparse groups
    if args.launch_task:
        bee_args.opt_launch(args)

    if args.terminate_task:
        bee_args.opt_terminate(args)

    # ensure status remains low in order
    if args.status:
        bee_args.opt_status()


def flow_default(args):
    BeeFlow(args.logflag, args.log_dest).main(args.launch_flow[0])


parser = argparse.ArgumentParser(description="BEE Launcher\n"
                                             "https://github.com/lanl/BEE")

###############################################################################
# Un-organized arguments that can be
#
# There is no logging support from the bee-launcher, it is only designed
# to be implemented and utilised by the "orchestrator"
###############################################################################
parser.add_argument("--logflag",
                    action="store_true",
                    default=False,
                    help="Flag logger (default=False)")
parser.add_argument("--logfile",
                    dest='log_dest', nargs=1,
                    default="/var/tmp/bee.log",
                    help="Target destination for log file (default=/var/tmp/bee.log)")


###############################################################################
# Subparser (main)
# NOTE: To my knowledge Python 2.7 does not support optional subparser groups
# This means the use is required to select on of the below options when
# launching the application or an error will be thrown
#
# Each original python module that had handled arguments has had that
# functionality removed along with any corresponding __main__.
# Translation: module -> subparser
#   bee_launcher.py  ->  launch
#   bee_flow.py  -> flow
#   bee_ci_launcher.py  -> swarm
###############################################################################
subparser = parser.add_subparsers(title="BEE Modules")
sub_launch_group = subparser.add_parser("launch",
                                        help="bee_launch.py")
sub_flow_group = subparser.add_parser("flow",
                                      help="bee_flow.py")


###############################################################################
# Bee Launcher
# Launching/removing a task is currently only supported individually, thus
# they should remain mutually exclusive (launch_group)
###############################################################################
launch_group = sub_launch_group.add_mutually_exclusive_group()
launch_group.add_argument("-l", "--launch",
                          dest='launch_task', nargs=1,
                          type=verify_single_beefile,
                          help="Runs task specified by <LAUNCH_TASK>.beefile, "
                               "that needs to be in the current directory")
launch_group.add_argument("-t", "--terminate",
                          dest='terminate_task', nargs=1,
                          help="Terminate tasks <TERMINATE_TASK>")
sub_launch_group.add_argument("-s", "--status",
                              action='store_true',
                              help="List all tasks with status, automatically "
                                   "updates status")
sub_launch_group.set_defaults(func=launch_default)


###############################################################################
# Bee Flow (composer)
###############################################################################
sub_flow_group.add_argument("-f", "--beeflow",
                            dest='launch_flow', nargs=1,
                            type=verify_single_beeflow,
                            help="Runs task specified by <LAUNCH_FLOW>.beeflow, "
                                 "that needs to be in the current directory")
sub_flow_group.set_defaults(func=flow_default)


def main():
    try:
        args = parser.parse_args()
        args.func(args)
    except AttributeError:
        cprint("Command line arguments required", "red")
        parser.parse_args(['-h'])
    except argparse.ArgumentError as e:
        cprint(e, "red")
        exit(1)


if __name__ == "__main__":
    main()
