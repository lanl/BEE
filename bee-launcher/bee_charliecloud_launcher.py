# system
import os
import getpass
import tarfile
from termcolor import cprint
# project
from bee_cluster import BeeTask
from bee_charliecloud import BeeCharliecloud


# Manipulates all nodes in a task
class BeeCharliecloudLauncher(BeeTask):
    def __init__(self, task_id, beefile, use_existing=False):
        BeeTask.__init__(self)

        self.__current_status = 0  # initializing

        self.__platform = 'BEE-Charliecloud'

        # User configuration
        self.__task_conf = beefile['task_conf']
        self.__bee_charliecloud_conf = beefile['exec_env_conf']['bee_charliecloud']
        self.__task_name = self.__task_conf['task_name']
        self.__task_id = task_id

        # Task configuration
        self.__hosts = self.__fetch_beefile_value("node_list",
                                                  self.__bee_charliecloud_conf,
                                                  ["localhost"])
        # __host_mpi formatted to be used with mpirun -host *
        # filled during launch event (string, to be used in cmd list)
        self.__hosts_mpi = None

        # Container configuration
        self.__container_path = beefile['container_conf']['container_path']
        self.__container_name = self.__verify_container_name()
        self.__ch_dir = self.__fetch_beefile_value("container_tar2dir",
                                                   self.__bee_charliecloud_conf,
                                                   "/var/tmp")  # ch-tar2dir
        self.__delete_after = self.__fetch_beefile_value("delete_after_exec",
                                                         self.__task_conf, False)

        # System configuration
        self.__user_name = getpass.getuser()
        self.__use_existing = use_existing

        # bee-charliecloud
        self.__bee_cc_list = []

        self.current_status = 1  # initialized

    # Accessors kept for historical reasons
    # Whenever possible we should remove these
    # or convert them to @property
    def get_current_status(self):
        return self.__current_status

    def get_platform(self):
        return self.__platform

    def get_end_event(self):
        return self.end_event

    def get_begin_event(self):
        return self.begin_event

    # Wait events (support for existing bee_orc_ctl)
    def add_wait_event(self, new_event):
        self.event_list = new_event

    # Task management
    def run(self):
        self.launch()

    def launch(self):
        self.terminate(clean=(not self.__use_existing))
        self.__current_status = 3  # Launching

        cprint("Charliecloud launching", self.output_color)

        # Fill bee_cc_list of running hosts (nodes)
        # Each element is an BeeCharliecloud object
        for host in self.__hosts:
            curr_rank = len(self.__bee_cc_list)
            self.__hosts_mpi = str(host) + ","
            if curr_rank == 0:
                hostname = "{}=bee-head".format(self.__task_name)
            else:
                hostname = "{}-bee-worker{}".format(self.__task_name,
                                                    str(curr_rank).zfill(3))
            # Each object represent a node
            bee_cc = BeeCharliecloud(task_id=self.__task_id, hostname=hostname,
                                     host=host, rank=curr_rank, task_conf=self.__task_conf,
                                     bee_cc_conf=self.__bee_charliecloud_conf,
                                     container_name=self.__container_name)
            # Add new CC to host
            self.__bee_cc_list.append(bee_cc)
            bee_cc.master = self.__bee_cc_list[0]

        # Check if there is an allocation to unpack images on
        if 'SLURM_JOBID' in os.environ:
            cprint(os.environ['SLURM_NODELIST'] + ": Launching " +
                   str(self.__task_name), self.output_color)

            # use_existing (invoked via flag at runtime)
            # leverages an already existing unpacked image
            if not self.__use_existing:
                self.__unpack_ch_dir(self.__hosts_mpi)
            self.wait_for_others()
            self.run_scripts()
        elif self.__hosts == ["localhost"]:  # single node or local instance
            cprint("Launching local instance " + str(self.__task_name),
                   self.output_color)
            self.__local_launch()
            self.run_scripts()
        else:
            cprint("No nodes allocated!", self.error_color)
            self.terminate()

    def run_scripts(self):
        self.__current_status = 4  # Running
        self.begin_event = True
        # Batch mode and MPI run can bother defined and ran together
        # in the same beefile; however, batch mode is exclusive
        if self.__task_conf['batch_mode']:
            self.batch_run()
        else:
            if self.__task_conf['mpi_run']:
                self.mpi_run()
            if self.__task_conf['general_run']:
                self.general_run()
        self.__current_status = 5  # finished
        cprint("[" + self.__task_name + "] end event", self.output_color)
        self.end_event = True
        if self.__delete_after:
            self.terminate()

    def general_run(self):
        """
        General sequential script run on each node
        """
        for run_conf in self.__task_conf['general_run']:
            for host in self.__bee_cc_list:
                host.general_run(run_conf['script'],
                                 local_pfwd=run_conf['local_port_fwd'],
                                 remote_pfwd=run_conf['remote_port_fwd'])

    def mpi_run(self):
        """
        MPI script run on each node declared
        """
        valid_map = ['socket', 'node']
        for run_conf in self.__task_conf['mpi_run']:
            script_path = run_conf['script']
            cmd = ['mpirun']
            ###################################################################
            # Check mpi options for mpi_run all tasks:
            #
            # The checks are done after running general_run tasks.
            # If map_by is invalid - terminate
            # If map_by is set but map_num is not - ignore map_by
            # If map_by is not set but map_num is not - terminate
            ###################################################################
            if 'node_list' in run_conf:
                my_nodes = ",".join(run_conf['node_list'])
                cmd.append("-host")
                cmd.append(my_nodes)

            if 'map_by' in run_conf:
                if run_conf['map_by'] not in valid_map:
                    cprint("For mpi_run the 'map_by' option is not valid!", "red")
                    print("Use a valid option or remove 'map_by'" +
                          " and 'map_num' to use default.")
                    self.terminate()

                elif 'map_num' not in run_conf:
                    cprint("For mpi_run 'map_num' is not set " +
                           "'map_by' is ignored!", self.error_color)

                else:
                    cmd.append("-map-by")
                    cmd.append("ppr:{}:{}".format(str(run_conf['map_num']),
                                                  run_conf['map_by']))

            elif 'map_num' in run_conf:
                cprint("For mpi_run when specifying 'map_num'," +
                       " 'map_by' must also be set!", self.error_color)
                self.terminate()

            cmd.append(script_path)
            self.run_popen_safe(cmd)

    def batch_run(self):
        # TODO: implement and test
        cprint("Batch mode not implemented for Bee_Chaliecloud yet!", "red")
        self.terminate()

    def terminate(self, clean=False):
        """
        Terminate the task
        Remove ALL
        :param clean: Flag if terminate function should be run
                but the status should NOT be set to terminated (6)
        """
        if self.__delete_after and self.__hosts_mpi is not None:
            # Remove ALL ch-directories found on nodes
            self.__remove_ch_dir(self.__hosts_mpi)
        if not clean:
            self.__current_status = 6  # Terminated

    def wait_for_others(self):
        self.current_status = 2  # Waiting
        for event in self.event_list:
            event.wait()

    # Task management support functions (private)
    def __local_launch(self):
        """
        Run Charliecloud exclusively using local instance
        Note, this is useful when attempting to use bee-cc
        outside of a HPC environment or single node
        """
        self.__unpack_ch_dir(self.__hosts)

    def __verify_container_name(self):
        """
        Using self.__container_path verify if the user specified is a valid
        tarball and extract the name that will be referenced by Charliecloud
        :return: If container correct, return name (without extension)
        """
        cp = self.__container_path

        if cp[-7:] == ".tar.gz" and tarfile.is_tarfile(cp):
            cp = cp[cp.rfind('/') + 1:-7]
            return cp
        else:
            cprint("Error: invalid container file format detected\n"
                   "Please verify the file is properly compressed (<name>.tar.gz)",
                   self.error_color)
            exit(1)

    def __unpack_ch_dir(self, hosts):
        """
        Unpack container via ch-tar2dir to defined directory
        :param hosts: Hosts/nodes on which the process should be invoked
                        format node1, node2, ...
        """
        cprint("Unpacking {} to {}".format(self.__container_name, self.__ch_dir),
               self.output_color)
        cmd = ['ch-tar2dir', self.__container_path, self.__ch_dir]
        if self.__hosts != ["localhost"]:
            ###############################################################
            # Temporary workaround due to perceived SSH limitation.
            # We will have to use mpirun for the time being.
            # TODO: implement non-mpi reliant method
            ###############################################################
            cmd = ['mpirun', '-host', hosts, '--map-by', 'ppr:1:node',
                   'ch-tar2dir', self.__container_path, self.__ch_dir]
            self.run_popen_safe(command=cmd, nodes=hosts)
        else:  # To be used when local instance of task only!
            self.run_popen_safe(command=cmd, nodes=str(self.__hosts))

    def __remove_ch_dir(self, hosts):
        """
        Remove directory created via ch-tar2dir (self.unpack()) on
        a single host, ignores non-existent directories without error
        :param hosts:   Hosts/nodes on which the process should be invoked
                        format node1, node2, ...
        """
        cprint("Removing any existing Charliecloud directory from {}".
               format(hosts), self.output_color)
        cmd = ['rm', '-rf', self.__ch_dir + "/" + self.__container_name]
        if self.__hosts != ["localhost"]:
            for host in self.__bee_cc_list:
                host.run(cmd, async=True)
        else:  # To be used when local instance of task only!
            self.run_popen_safe(command=cmd, nodes=str(self.__hosts))

    def __fetch_beefile_value(self, key, dictionary, default=None):
        """
        Fetch a specific key/value pair from the .beefile and
        raise error is no default supplied and nothing found
        :param key: Key for value in dictionary
        :param dictionary: dictionary to be searched
                            e.g. self.__beefile['task_conf']
        :param default: Returned if no value found, if None (def)
                        then error message surfaced
        :return: Value for key. Data type dependent on beefile,
                    and no verification beyond existence
        """
        try:
            return dictionary[key]
        except KeyError:
            if default is not None:
                cprint("User defined value for [" + str(key) +
                       "] was not found, default value: " + str(default) +
                       " used.", self.warning_color)
                return default
            else:
                cprint("Key: " + str(key) + " was not found in: " +
                       str(dictionary), self.error_color)
