#!/usr/bin/env python
import pexpect
import Pyro4
import Pyro4.naming
import subprocess
import getpass
from subprocess import Popen
from bee_aws_launcher import BeeAWSLauncher 
from bee_vm_launcher import BeeVMLauncher
from bee_os_launcher import BeeOSLauncher
#from bee_charliecloud_launcher import BeeCharliecloudLauncher
import boto3
from threading import Thread
from bee_task import BeeTask
import os
import getpass
import json
import time
@Pyro4.expose
class BeeLauncherDaemon(object):
    def __init__(self):
        print("Starting Bee orchestration controller..")
        self.__beetasks = {}
        print(os.path.dirname(os.path.abspath(__file__)))
        self.__py_dir = os.path.dirname(os.path.abspath(__file__))

    def create_task(self, beefile, restore = False):
        print("Bee orchestration controller: received task creating request")
        exec_target = beefile['task_conf']['exec_target']
        beetask_name = beefile['task_conf']['task_name']
        total_tasks = len(self.__beetasks)
        if exec_target == 'bee_vm':
            beetask = BeeVMLauncher(total_tasks + 1, beefile, restore)
            self.__beetasks[beetask_name] = beetask
            return beetask
        elif exec_target == 'bee_aws':
            beetask = BeeAWSLauncher(total_tasks + 1, beefile)
            self.__beetasks[beetask_name] = beetask
            return beetask
        elif exec_target == 'bee_os':
            beetask = BeeOSLauncher(total_tasks + 1, beefile)
            self.__beetasks[beetask_name] = beetask
            return beetask
        #elif exec_target == 'bee_charliecloud':
        #    beetask = BeeCharliecloudLauncher(total_tasks + 1, beefile, restore)
        #    self.__beetasks[beetask_name] = beetask
        #    return beetask

# Need error checking for none of the above
        
    def launch_task(self, beetask):
        beetask.start()
    
    def create_and_launch_task(self, beefile, restore = False):
        beetask = self.create_task(beefile, restore)
        self.launch_task(beetask)

    def checkpoint_task(self, beetask_name):
        self.__beetasks[beetask_name].checkpoint()

    def terminate_task(self, beetask_name):
        beetask = self.__beetasks[beetask_name].terminate()

    def delete_task(self, beetask_name):
        beetask = self.__beetasks[beetask_name].terminate()
        del self.__beetasks[beetask_name]

    def list_all_tasks(self):
        tasks_and_status = {}
        for beetask_name in self.__beetasks:
            tasks_and_status[beetask_name] = {"status" : self.__beetasks[beetask_name].get_current_status(),
                                              "platform" : self.__beetasks[beetask_name].get_platform()}
        return tasks_and_status

    def create_bee_aws_storage(self, efs_name, perf_mode = 'generalPurpose'):
        print("Bee orchestration controller: received bee-aws storage creating request")
        if self.get_bee_efs_id(efs_name) != -1:
            print("EFS named " + efs_name + " already exist!")
            return  '-1'
        efs_client = boto3.client('efs')
        efs_client.create_file_system(CreationToken = efs_name, PerformanceMode = perf_mode)
        resp = efs_client.describe_file_systems(CreationToken = efs_name)
        efs_id = resp['FileSystems'][0]['FileSystemId']
        efs_client.create_tags(FileSystemId = efs_id,
                               Tags=[{'Key':'Name', 'Value':efs_name}])
        self.wait_bee_efs(efs_name)
        print('Created new BEE EFS:' + efs_id)
        return efs_id

    # Get the id of bee efs, if not exist, -1 is returned.                     
    def get_bee_efs_id(self, efs_name):
        all_efss = boto3.client('efs').describe_file_systems()
        bee_efs_id = -1
        for efs in all_efss['FileSystems']:
            if efs['CreationToken'] == efs_name:
                bee_efs_id = efs['FileSystemId']
        return bee_efs_id

    def wait_bee_efs(self, efs_name):
        print("Wait for EFS to become available.")
        efs_client = boto3.client('efs')
        resp = efs_client.describe_file_systems(CreationToken = efs_name)
        state = resp['FileSystems'][0]['LifeCycleState']
        while state != 'available':
            resp = efs_client.describe_file_systems(CreationToken = efs_name)
            state = resp['FileSystems'][0]['LifeCycleState']

    def launch_efs_daemon(self, efs_id):
        efs_daemon_beefile = os.path.dirname(os.path.abspath(__file__)) + "efs-daemon.beefile"
        f = open(efs_daemon_beefile, "r")
        beefile = json.load(f)

    def launch_beeflow(self, beeflow, beefiles):
        # Initialize each task
        beeflow_tasks = {}
        for task_name in beefiles:
            beefile = beefiles[task_name]
            beetask = self.create_task(beefile)
            beeflow_tasks[task_name] = beetask
            self.__beetasks[task_name] = beetask
            
        # Create dependency
        for task_name in beeflow:
            beetask = beeflow_tasks[task_name]
            dependency_list = beeflow[task_name]['dependency_list']
            if len(beeflow[task_name]['dependency_list']) > 0:
                dependency_mode = beeflow[task_name]['dependency_mode']
                for dependent_name in dependency_list:
                    dependent_beetask = beeflow_tasks[dependent_name]
                    if dependency_mode == "off-line":
                        print("Creating off-line dependecy:" + task_name + " --> " + dependent_name + ".")
                        end_event = dependent_beetask.get_end_event()
                        beetask.add_wait_event(end_event)
                    elif dependency_mode == "in-situ":
                        print("Creating in-situ dependecy:" + task_name + " --> " + dependent_name + ".")
                        begin_event = dependent_beetask.get_begin_event()
                        beetask.add_wait_event(begin_event)
        
        # Launch tasks
        for task_name in beeflow_tasks:
            self.launch_task(beeflow_tasks[task_name])

def main():
    open_port = get_open_port()
    update_system_conf(open_port)
    #Pyro4.naming.startNSloop(port = open_port, hmac = getpass.getuser())
    Popen(['python', '-m', 'Pyro4.naming', '-k', getpass.getuser(), '-p', str(open_port)])
    time.sleep(1)
    bldaemon = BeeLauncherDaemon()
    daemon = Pyro4.Daemon()
    bldaemon_uri = daemon.register(bldaemon)
    ns = Pyro4.locateNS(port = open_port, hmac_key = getpass.getuser())
    ns.register("bee_launcher.daemon", bldaemon_uri)
    print("Bee orchestration controller started.")    
    daemon.requestLoop()
    
def update_system_conf(open_port):
    pydir = os.path.dirname(os.path.abspath(__file__))
    f = open(pydir + "/bee_conf.json", "r")
    data = json.load(f)
    f = open(pydir + "/bee_conf.json", "w")
    data["pyro4-ns-port"] = open_port
    json.dump(data, f)

def get_open_port():
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("",0))
        s.listen(1)
        port = s.getsockname()[1]
        s.close()
        return port

if __name__=="__main__":
    main()
