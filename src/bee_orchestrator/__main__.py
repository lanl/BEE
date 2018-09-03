# system
import argparse
from termcolor import cprint
from os import path, remove, chdir
# project
from .bee_orc_ctl import main as boc
from beefile_manager import BeefileLoader


# Parser supporting functions / classes
def verify_pyro4_conf():
    """
    Create json file used to share port set by Pryo4 across
    instance running orchestrator
    """
    conf_file = str(path.expanduser('~')) + "/.bee/port_conf.json"
    if path.isfile(conf_file):
        remove(conf_file)
    with open(conf_file, 'w') as file:
        file.write("{\"pyro4-ns-port\": 12345}")


parser = argparse.ArgumentParser(description="BEE Orchestrator\n"
                                             "https://github.com/lanl/BEE")


###############################################################################
# Bee Orchestrator
#
# orc: Launch standard BEE Orchestrator
# orc_arm: Launch ARM specific BEE Orchestrator
#
# task: Including this option allows for a bee specific task
#       (.beefile) that will automatically be launched to the orchestrator
###############################################################################
orc_group = parser.add_mutually_exclusive_group()
orc_group.add_argument("-o", "--orc",
                       action='store_true',
                       help="Launch Bee Orchestrator Controller")
orc_group.add_argument("-oa", "--orc_arm",
                       action='store_true',
                       help="Launch Bee Orchestrator Controller for ARM")

parser.add_argument("-t", "--task",
                    dest='task', nargs=1,
                    default=None,
                    help="Bee task (.beefile) you will to execute via orchestrator")

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


def manage_args(args):
    # check file requirements
    verify_pyro4_conf()

    if args.task is not None:
        if args.orc:
            p = args.task[0]
            t = p.rfind("/")
            chdir(p[:t])
            f = BeefileLoader(args.task[0])
            boc(f.beefile, p[t+1:len(p)])
        elif args.orc_arm:
            cprint("ARM support not ready at the moment!", 'red')
        else:
            cprint("Please specify a valid orchestrator!", 'red')

    elif args.orc:
        boc()
    elif args.orc_arm:
        cprint("ARM support not ready at the moment!", 'red')

    # Enable only when log flag is set true!
    if args.logflag is True:
        cprint("Logging not implemented yet\n"
               "Logflag = " + str(args.logflag) +
               "\nLogfile = " + args.log_dest, 'red')


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
