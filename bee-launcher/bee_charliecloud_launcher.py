# system
import subprocess
import os
import getpass
from termcolor import cprint
from threading import Event
# project
from bee_task import BeeTask


class BeeCharliecloudLauncher(BeeTask):
    def __init__(self, task_id, beefile, restore=False):
        BeeTask.__init__(self)

        self.__platform = 'BEE-Charliecloud'

        self.__current_status = 0  # initializing

        # User configuration
        self.__task_conf = beefile['task_conf']
        self.__bee_charliecloud_conf = beefile['exec_env_conf']['bee_charliecloud']
        self.__task_name = self.__task_conf['task_name']
        self.__task_id = task_id
        try:
            self.__hosts = self.__bee_charliecloud_conf['node_list']
        except:
            self.__hosts = ["localhost"]

        # User configuration - container information
        self.__container_path = beefile['container_conf']['container_path']
        self.__container_name = self.__verify_container_name()

        # System configuration
        self.__user_name = getpass.getuser()
        self.__restore = restore
        self.__ch_dir = '/var/tmp'  # ch-tar2dir

        # Output colors
        self.__output_color_list = ["magenta", "cyan", "blue", "green",
                                    "red", "grey", "yellow"]
        self.__output_color = "cyan"

        # Events for workflow
        self.__begin_event = Event()
        self.__end_event = Event()
        self.__event_list = []

        self.__current_status = 1  # initialized

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
        self.__current_status = 3  # Launching
        print "Charliecloud configuration done"

        # Check if there is an allocation to unpack images on
        # TODO: review goal and possible elif (e.g. local, non-mpi)
        if 'SLURM_JOBID' in os.environ:
            cprint(os.environ['SLURM_NODELIST'] + ": Launching " +
                   str(self.__task_name), "cyan")

            # if -r re-use image other wise unpack image
            # not really a restore yet 
            if not self.__restore:
                for hosts in self.__hosts:
                    self.unpack_image(hosts)
            self.run_scripts()

        else:
            cprint("No nodes allocated!", "red")
            self.terminate()

    def unpack_image(self, host):
        # TODO: identify best method for async commands
        # Unpack image on each allocated node
        cprint("Unpacking container to {}".format(host), self.__output_color)
        cmd = ['mpirun', '-host', host, '--map-by', 'ppr:1:node',
               'ch-tar2dir', self.__container_path, self.__ch_dir]

        try:
            subprocess.call(cmd)
        except:
            cprint(" Error while unpacking image:", "red")

    def run_scripts(self):
        self.__current_status = 4  # Running
        self.__begin_event.set()
        if self.__task_conf['batch_mode']:
            self.batch_run()
        else:
            self.general_run()
        self.__current_status = 5  # finished
        self.__end_event.set()

    def general_run(self):
        # General script

        for run_conf in self.__task_conf['general_run']:
            script_path = run_conf['script']
            cmd = ['sh', script_path]
            subprocess.call(cmd)

        '''  
        Check mpi options for mpi_run all tasks:

        The checks are done after running general_run tasks.
        If map_by is invalid - terminate
        If map_by is set but map_num is not - ignore map_by 
        If map_by is not set but map_num is not - terminate
        '''

        valid_map = ['socket', 'node']
        for run_conf in self.__task_conf['mpi_run']:
            script_path = run_conf['script']
            cmd = ['mpirun']

            # run on node_list
            if 'node_list' in run_conf:
                my_nodes = ",".join(run_conf['node_list'])
                cmd.append("-host")
                cmd.append(my_nodes)

            # run on node_list

            if 'map_by' in run_conf:
                if run_conf['map_by'] not in valid_map:
                    cprint("For mpi_run the 'map_by' option is not valid!", "red")
                    print("Use a valid option or remove 'map_by'" +
                          " and 'map_num' to use default.")
                    self.terminate()

                elif 'map_num' not in run_conf:
                    cprint("For mpi_run 'map_num' is not set " +
                           "'map_by' is ignored!", "red")

                else:
                    cmd.append("-map-by")
                    cmd.append("ppr:{}:{}".format(str(run_conf['map_num']),
                                                  run_conf['map_by']))

            elif 'map_num' in run_conf:
                cprint("For mpi_run when specifying 'map_num'," +
                       " 'map_by' must also be set!", "red")
                self.terminate()

            cmd.append(script_path)

            try:
                subprocess.call(cmd)
            except:
                cprint(" Error running script:" + script_path, "red")
                cprint(" Check path to mpirun.", "red")

    def batch_run(self):
        cprint("Batch mode not implemented for Bee_Chaliecloud yet!", "red")
        self.terminate()

    def __verify_container_name(self):
        """
        Using self.__container_path verify if the user specified is a valid
        tarball and extract the name that will be referenced by Charliecloud
        :return: If container correct, return name (without extension)
        """
        cp = self.__container_path

        if cp[-7:] is ".tar.gz":
            cp = cp[cp.rfind('/') + 1:-7]
            return cp
        # TODO: check if tar via python?
        else:
            cprint("Error: invalid container file format detected", "red")
            exit(2)  # TODO: discuss error codes

    def __remove_ch_dir(self, host_node):  # TODO: move to node specific class?
        """
        Remove directory created via ch-tar2dir (self.unpack()) on
        a single host, ignores non-existent directories without error
        :param host_node: Host/node on which the process should be invoked
        """
        cprint("Removing any existing Charliecloud directory from {}".
               format(host_node), self.__output_color)
        cmd = ['mpirun', '-host', host_node, '--map-by', 'ppr:1:node',
               'rm' '-rf', self.__container_name]

        try:
            subprocess.call(cmd)
        except:
            cprint("Error: unable to remove Charliecloud created directory",
                   "red")

    def terminate(self, clean=False):
        for host_node in self.__hosts:
            self.__remove_ch_dir(host_node)
            if not clean:
                self.__current_status = 6  # Terminated
