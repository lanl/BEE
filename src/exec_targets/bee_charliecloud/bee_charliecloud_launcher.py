# system
import os
import tarfile
from termcolor import cprint
# project
from bee_cluster import BeeTask
from bee_charliecloud_node import BeeCharliecloudNode


# Manipulates all nodes in a task
class BeeCharliecloudLauncher(BeeTask):
    def __init__(self, task_id, beefile):
        BeeTask.__init__(self, task_id=task_id, beefile=beefile)

        self.__current_status = 0  # initializing

        # Task configuration
        self.platform = 'BEE-Charliecloud'

        # Container configuration
        # TODO: add verification steps
        self.__cc_source = self._beefile['requirements']['CharliecloudRequirement']\
            .get('tarDir')
        self.__cc_tarDir = self._beefile['requirements']['CharliecloudRequirement']\
            .get('tarDir', '/var/tmp')
        self.__delete_after = self._beefile['requirements']['CharliecloudRequirement']\
            .get('deleteAfter', True)
        self.__container_name = self.__verify_container_name()

        # bee-charliecloud
        self.__bee_cc_list = []

        self.current_status = 1  # initialized

    # Wait events (support for existing bee_orc_ctl)
    def add_wait_event(self, new_event):
        self.event_list = new_event

    # Task management
    def run(self):
        self.launch()

    def launch(self):
        self.terminate()
        self.__current_status = 3  # Launching

        cprint("[" + self._task_id + "] Charliecloud launching", self.output_color)

        # Fill bee_cc_list of running hosts (nodes)
        # Each element is an BeeCharliecloud object
        for host in self.__hosts:
            curr_rank = len(self.__bee_cc_list)
            self.__hosts_mpi += str(host) + ","
            self.__hosts_total += 1
            if curr_rank == 0:
                hostname = "{}=bee-head".format(self.__task_name)
            else:
                hostname = "{}-bee-worker{}".format(self.__task_name,
                                                    str(curr_rank).zfill(3))
            # Each object represent a node
            bee_cc = BeeCharliecloudNode(task_id=self.__task_id, hostname=hostname,
                                     host=host, rank=curr_rank, task_conf=self.__task_conf,
                                     bee_cc_conf=self.__bee_charliecloud_conf,
                                     container_name=self.__container_name)
            # Add new CC to host
            self.__bee_cc_list.append(bee_cc)
            bee_cc.master = self.__bee_cc_list[0]

        # Remove erroneous comma (less impact), for readability
        if self.__hosts_mpi[-1] == ",":
            self.__hosts_mpi = self.__hosts_mpi[:-1]

        cprint("Preparing launch " + self._task_id + " for nodes "
               + self.__hosts_mpi, self.output_color)

        # Check if there is an allocation to unpack images on
        if 'SLURM_JOBID' in os.environ:
            cprint(os.environ['SLURM_NODELIST'] + ": Launching " +
                   str(self.__task_name), self.output_color)

            # use_existing (invoked via flag at runtime)
            # leverages an already existing unpacked image
            if not self.__use_existing:
                self.__unpack_ch_dir(self.__hosts_mpi, self.__hosts_total)
            self.wait_for_others()
            self.run_scripts()
        elif self.__hosts == ["localhost"]:  # single node or local instance
            cprint("Launching local instance " + str(self.__task_name),
                   self.output_color)
            self.__local_launch()
            self.run_scripts()
        else:
            cprint("[" + self.__task_name + "] No nodes allocated!", self.error_color)
            self.terminate()

    def run_scripts(self):
        self.__current_status = 4  # Running
        self.begin_event = True
        # General, SRUN, and MPI run can be run together & defined
        # in the same beefile; however, batch mode is exclusive
        if self.__task_conf['batch_mode']:
            self.batch_run()
        else:
            if self.__task_conf['general_run']:
                self.general_run()
            try:  # optional to avoid affecting existing
                if self.__task_conf['srun_run']:
                    self.srun_run()
            except KeyError:
                pass
            if self.__task_conf['mpi_run']:
                self.mpi_run()
        self.__current_status = 5  # finished
        cprint("[" + self.__task_name + "] end event", self.output_color)
        self.end_event = True
        if self.__delete_after:
            self.terminate()

    def batch_run(self):
        # TODO: implement and test ?
        cprint("Batch mode not implemented for Bee_Chaliecloud yet!", 'red')
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
            self.__remove_ch_dir(self.__hosts_mpi, self.__hosts_total)
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
        self.__unpack_ch_dir(self.__hosts, 1)

    def __verify_container_name(self):
        """
        Using self.__container_path verify if the user specified is a valid
        tarball and extract the name that will be referenced by Charliecloud
        :return: If container correct, return name (without extension)
        """
        cp = self.__cc_source

        if cp[-7:] == ".tar.gz" and tarfile.is_tarfile(cp):
            cp = cp[cp.rfind('/') + 1:-7]
            return cp
        else:
            cprint("Error: invalid container file format detected\n"
                   "Please verify the file is properly compressed (<name>.tar.gz)",
                   self.error_color)
            exit(1)

    def __remove_ch_dir(self, hosts, total_hosts):
        """
        Remove directory created via ch-tar2dir (self.unpack()) on
        a single host, ignores non-existent directories without error
        :param hosts:   Hosts/nodes on which the process should be invoked
                        format node1, node2, ...
        :param total_hosts: Min/Max number of nodes/hosts to be allocation
                            Should match the number of nodes listed in
                            the hosts string parameter
        """
        cprint("[" + self._task_id  + "] Removing any existing Charliecloud"
                                        " directory from {}".format(hosts), self.output_color)
        cmd = ['rm', '-rf', self.__ch_dir + "/" + self.__container_name]
        if self.__hosts != ["localhost"]:
            self.run_popen_safe(command=self.compose_srun(cmd, hosts, total_hosts),
                                nodes=hosts)
        else:  # To be used when local instance of task only!
            self.run_popen_safe(command=cmd, nodes=str(self.__hosts))

    def __fetch_beefile_value(self, key, dictionary, default=None, quit_err=False,
                              silent=False):
        """
        Fetch a specific key/value pair from the .beefile and
        raise error is no default supplied and nothing found
        :param key: Key for value in dictionary
        :param dictionary: dictionary to be searched
                            e.g. self.__beefile['task_conf']
        :param default: Returned if no value found, if None (def)
                        then error message surfaced
        :param quit_err: Exit with non-zero (default=False)
        :param silent: Hide warning message (default=False)
        :return: Value for key. Data type dependent on beefile,
                    and no verification beyond existence
        """
        try:
            return dictionary[key]
        except KeyError:
            if default is not None and not quit_err:
                if not silent:
                    cprint("[" + self._task_id + "] User defined value for ["
                           + str(key) + "] was not found, default value: "
                           + str(default) + " used.", self.warning_color)
                return default
            else:
                cprint("[" + self._task_id + "] Key: " + str(key) + " was not found in: " +
                       str(dictionary), self.error_color)
                exit(1)
