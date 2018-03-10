from bee_charliecloud import BeeCharliecloud
import time
import subprocess
#from subprocess import Popen
import os
from termcolor import colored, cprint
#from os.path import expanduser
#from threading import Thread
from threading import Event
from bee_task import BeeTask


class BeeCharliecloudLauncher(BeeTask):
    def __init__(self, task_id, beefile, restore = False):
        BeeTask.__init__(self)
        self.__platform = 'BEE-Charliecloud'
        self.__current_status = 0 # initializing

        # User configuration
        self.__task_conf = beefile['task_conf']
        self.__bee_charliecloud_conf = beefile['exec_env_conf']['bee_charliecloud']
        self.__container_path = beefile['container_conf']['container_path']
        self.__task_name = self.__task_conf['task_name']
        self.__task_id = task_id

        # System configuration
        self.__user_name = os.getlogin()
        self.__restore = restore
        
        # Events for workflow
        self.__begin_event = Event()
        self.__end_event = Event()
        self.__event_list = []

        self.__current_status = 1 # initialized
    
    def get_begin_event(self):
        return self.__begin_event

    def get_end_event(self):
        return self.__end_event

    def add_wait_event(self, new_event):
        self.__event_list.append(new_event)

    def get_current_status(self):
        return self.__current_status

    def get_platform(self):
        return self.__platform

    def run(self):
        self.launch()

    def launch(self):
        self.__current_status = 3 # Launching
        print "charliecloud conf done"

        # Check if there is an allocation to unpack images on        
        if 'SLURM_JOBID' in os.environ:
            cprint (os.environ['SLURM_NODELIST'] + ": Launching " + 
                str(self.__task_name) ,"cyan")

            # if -r re-use image other wise unpack image
            # not really a restore yet 
            if not self.__restore:
                self.unpack_image()
            self.run_scripts()

        else:
            cprint ("No nodes allocated!","red")
            self.terminate()

    def unpack_image(self):
        cmd = ['srun','ch-tar2dir', self.__container_path, '/var/tmp']
        subprocess.call(cmd)

    def run_scripts(self):
        self.__current_status = 4 #Running
        self.__begin_event.set()
        if self.__task_conf['batch_mode']:
            self.batch_run()
        else:
            self.general_run()
        self.__current_status = 5 # finished
        self.__end_event.set()


    def general_run(self):
        # General script
        for run_conf in self.__task_conf['general_run']:
            script_path = run_conf['script']
            cmd = ['sh', script_path ]
            subprocess.call(cmd)

        for run_conf in self.__task_conf['mpi_run']:
            cprint("Bee_Charliecloud does not support mpi_run option!","red")
            cprint("Use general_run and specify mpirun command in script.", "red")


    def batch_run(self):
        cprint ("Batch mode not implemented for Bee_Chaliecloud yet!","red")
        self.terminate()
   
    def terminate(self, clean = False):
        if not clean:
            self.__current_status = 6 #Terminated
