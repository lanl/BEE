from bee_charliecloud import BeeCharliecloud
#from host import Host
import time
import subprocess
import os
from os.path import expanduser
from threading import Thread
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
        self.__container_conf = beefile['container_conf']
        self.__hosts = self.__bee_charliecloud_conf['node_list']
        self.__task_name = self.__task_conf['task_name']
        self.__task_id = task_id

        # System configuration
        self.__user_name = os.getlogin()
        self.__bee_working_dir = expanduser("~") + "/.bee"
        self.__charliecloud_key_path = self.__bee_working_dir + "/ssh_key/id_rsa"
        self.__tmp_dir = self.__bee_working_dir + "/tmp"
        self.__restore = restore
        print("HERE CCL init:", str(self.__bee_charliecloud_conf))

        
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
        self.terminate(clean = True)
        self.__current_status = 3 # Launching
        
        print ("HERE CCL")
        print "charlecloud conf done"
        exit()
        time.sleep(1)

    def terminate(self, clean = False):
            if not clean:
                self.__current_status = 6 #Terminated
