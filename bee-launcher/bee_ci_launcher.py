#!/usr/bin/env python
import subprocess
from subprocess import Popen
from bee_aws_launcher import BeeAWSLauncher 
from bee_vm_launcher import BeeVMLauncher
from bee_os_launcher import BeeOSLauncher
from beefile_loader import BeefileLoader
import boto3
from threading import Thread
from bee_task import BeeTask
import os
import json
import time
import sys
import getopt
import os
import json

class BeeCILauncher(object):
    def __init__(self):
        print("Launching BEE task on CI.")
        self.beetask = ""
        self.reservation_id = ""

    def create_task(self, beefile):
        print("Bee orchestration controller: received task creating request")
        exec_target = beefile['task_conf']['exec_target']
        beetask_name = beefile['task_conf']['task_name']
        if exec_target == 'bee_vm':
            self.beetask = BeeVMLauncher(0, beefile)
        elif exec_target == 'bee_aws':
            self.beetask = BeeAWSLauncher(0, beefile)
        elif exec_target == 'bee_os':
            self.beetask = BeeOSLauncher(0, beefile)
           
    def launch_task(self):
        self.beetask.start()
    
    def create_and_launch_task(self, beefile):
        self.create_task(beefile)
        self.launch_task()

    def terminate_task(self, beetask_name):
        self.beetask.terminate()

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "l:r:", ["launch=", "reservation="])
    except getopt.GetoptError:
        print("Please provide beefile or efs name.")
        exit()

    reservation_id = ""
    for opt, arg in opts: 
        if opt in ("-r", "--reservation"):
            reservation_id = arg

    for opt, arg in opts: 
        if opt in ("-l", "--launch"):
            beefile = arg
            print("Sending launching request.")
            beefile_loader = BeefileLoader(beefile)
            beefile = beefile_loader.get_beefile()
            if (reservation_id != ""):
                beefile["exec_env_conf"]["bee_os"]["reservation_id"] = reservation_id
            bee_ci_launcher = BeeCILauncher()
            bee_ci_launcher.create_and_launch_task(beefile)
            exit()

if __name__ == "__main__":
    main(sys.argv[1:])