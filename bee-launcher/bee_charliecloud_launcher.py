from bee_charliecloud import BeeCharliecloud
import time
import subprocess
#from subprocess import Popen
import os
import getpass
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
        self.__user_name = getpass.getuser()
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
        print "Charliecloud configuration done"

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
        #Unpack image on each allocated node
        cmd = ['mpirun','--map-by','ppr:1:node',
               'ch-tar2dir', self.__container_path, '/var/tmp']

        
        try:
            subprocess.call(cmd)
        except:
            cprint(" Error while unpacking image:","red")

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

        # Check mpi options for mpi_run all tasks

        # The checks are done after running general_run tasks  
        # If map_by is invalid - terminate
        # If map_by is set but map_num is not - ignore map_by 
        # If map_by is not set but map_num is not - terminate

        valid_map = ['socket', 'node']
        for run_conf in self.__task_conf['mpi_run']:
            script_path = run_conf['script']
            cmd = ['mpirun']
 
            # run on node_list
            if 'node_list' in run_conf:
                my_nodes= ",".join(run_conf['node_list'])
                cmd.append("-host")
                cmd.append(my_nodes)
  
            # run on node_list

            if ('map_by' in run_conf): 
                if (run_conf['map_by'] not in valid_map):
                    cprint("For mpi_run the 'map_by' option is not valid!","red")
                    print("Use a valid option or remove 'map_by'"+
                          " and 'map_num' to use default.")
                    self.terminate() 

                elif ('map_num' not in run_conf):
                    cprint("For mpi_run 'map_num' is not set "+ 
                        "'map_by' is ignored!", "red")

                else:
                    cmd.append("-map-by") 
                    cmd.append("ppr:{}:{}".format(str(run_conf['map_num']),
                                run_conf['map_by']))
                    
            elif ('map_num' in run_conf):
                cprint("For mpi_run when specifying 'map_num',"+
                       " 'map_by' must also be set!", "red")
                self.terminate() 

            cmd.append(script_path)
            #cprint("cmd = "+str(cmd), "red")
            try:
                subprocess.call(cmd)
            except:
                cprint(" Error running script:" + script_path, "red")
                cprint(" Check path to mpirun.","red")


    def batch_run(self):
        cprint ("Batch mode not implemented for Bee_Chaliecloud yet!","red")
        self.terminate()
   
    def terminate(self, clean = False):
        if not clean:
            self.__current_status = 6 #Terminated
