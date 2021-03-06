#!/usr/bin/env python
import Pyro4
import Pyro4.naming
import getpass
from subprocess import Popen
from bee_charliecloud_launcher import BeeCharliecloudLauncher
import os
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
        if exec_target == 'bee_charliecloud':
            beetask = BeeCharliecloudLauncher(total_tasks + 1, beefile, restore)
            self.__beetasks[beetask_name] = beetask
            return beetask
        
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
                        print("Creating off-line dependency:" + task_name + " --> " + dependent_name + ".")
                        end_event = dependent_beetask.get_end_event()
                        beetask.add_wait_event(end_event)
                    elif dependency_mode == "in-situ":
                        print("Creating in-situ dependency:" + task_name + " --> " + dependent_name + ".")
                        begin_event = dependent_beetask.get_begin_event()
                        beetask.add_wait_event(begin_event)
        
        # Launch tasks
        for task_name in beeflow_tasks:
            self.launch_task(beeflow_tasks[task_name])


def main(log=True, log_des="/var/tmp/bee.log"):
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
