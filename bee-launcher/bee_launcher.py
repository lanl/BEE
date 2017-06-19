#!/usr/bin/python
from __future__ import print_function
import Pyro4
from beefile_loader import BeefileLoader
import sys
import getopt
import os
import json
from termcolor import colored, cprint
from tabulate import tabulate
import time


class BeeLauncher(object):
    def __init__(self):
        self.__pydir = os.path.dirname(os.path.abspath(__file__))
        self.__cwdir = os.getcwd()
        f = open(self.__pydir + "/bee_conf.json", "r")
        data = json.load(f)
        port = int(data["pyro4-ns-port"])
        ns = Pyro4.locateNS(port = port, hmac_key = os.getlogin())
        uri = ns.lookup("bee_launcher.daemon")
        self.bldaemon = Pyro4.Proxy(uri) #Pyro4.Proxy("PYRONAME:bee_launcher.daemon")
        self.__status = ["Initializing", "Initialized", "Waiting", "Launching", "Running", "Finished", "Terminated"]
        self.__status_color = ['grey', 'white', 'yellow', 'cyan', 'green', 'magenta', 'red']

    def launch(self, beefile):
        self.encode_cwd(beefile)
        self.bldaemon.create_and_launch_task(beefile)

    def list_all_tasks(self):
        return self.bldaemon.list_all_tasks()

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

def main(argv):
    status_list = ["Initializing", "Initialized", "Waiting", "Launching", "Running", "Finished", "Terminated"]
    status_color_list = ['grey', 'white', 'yellow', 'cyan', 'green', 'magenta', 'red']
    bee_launcher = BeeLauncher()
    beefile = ""
    try:
        opts, args = getopt.getopt(argv, "l:st:d:e:", ["launch=", "status", "terminate=", "delete=", "efs="])
    except getopt.GetoptError:
        print("Please provide beefile or efs name.")
        exit()

    for opt, arg in opts: 
        if opt in ("-l", "--launch"):
            beefile = arg
            print("Sending launching request.")
            beefile_loader = BeefileLoader(beefile)
            beefile = beefile_loader.get_beefile()
            bee_launcher.launch(beefile)
            exit()

        elif opt in ("-s", "--status"):
            while True:
                status = bee_launcher.list_all_tasks()
                if len(status) == 0:
                    print("No task exist.")
                    
                table = []
                    
                count = 1
                for beetask in status:
                    color_status = colored(status_list[status[beetask]], status_color_list[status[beetask]])
                    #print(str(count) + ". " + beetask + " [" + color_status + "]")
                    table.append([str(count), beetask, color_status])
                    count = count + 1
                os.system('clear')
                print(tabulate(table, headers=['No.', 'Task Name', 'Status']))
                time.sleep(1)
            exit()

        elif opt in ("-t", "--terminate"):
            beetask_name = arg
            print("Sending termination request.")
            bee_launcher.terminate_task(beetask_name)
            print("Task: " + beetask_name + " is terminated.")
            exit()

        elif opt in ("-d", "--delete"):
            beetask_name = arg
            print("Sending deletion request.")
            bee_launcher.delete_task(beetask_name)
            print("Task: " + beetask_name + " is deleted.")
            exit()

        elif opt in ("-e", "--efs"):
            efs_id = bee_launcher.create_bee_aws_storage(arg)
            if efs_id == "-1":
                print("EFS name already exists!")
            else:
                print("EFS created: " + efs_id)
            exit()

if __name__ == "__main__":
    main(sys.argv[1:])
