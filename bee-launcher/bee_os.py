import subprocess
from docker import Docker
import os
from termcolor import colored, cprint

class BeeOS(object):
    def __init__(self, task_id, hostname, rank, task_conf, bee_os_conf, key_path, private_ip, master_public_ip, master = ""):
        # Basic configurations
        self.status = ""
        self.hostname = hostname
        self.__rank = rank
        self.master = master
        self.__user_name = "cc"
        self.__key_path = key_path
        self.__remote_key_path = '/home/cc/.ssh/'

        # Network
        self.private_ip = private_ip
        self.master_public_ip = master_public_ip


        # Docker container
        self.__docker = ""

        self.__output_color = "cyan"

    def run_on_master(self, command, local_pfwd = [], remote_pfwd = [], async = False):
    	exec_cmd = ["ssh",
                    "-p {}".format(self.ssh_port),
                    "-o StrictHostKeyChecking=no",
                    "-o ConnectTimeout=300",
                    "-o UserKnownHostsFile=/dev/null",
                    "-q",
                    "-i {}".format(self.__key_path),
                    "{}@{}".format(self.__user_name, self.master_public_ip),
                    "-x"]
        for port in local_pfwd:
            exec_cmd.insert(7, "-L {}:localhost:{}".format(port, port))
        for port in remote_pfwd:
            exec_cmd.insert(7, "-R {}:localhost:{}".format(port, port))

        cmd = exec_cmd + ["'"] + command + ["'"]
        if async:
            return Popen(cmd)
        else:
            return subprocess.call(cmd)


    def run_on_worker(self, command, local_pfwd = [], remote_pfwd = [], async = False):
    	exec_cmd = ["ssh",
                    "-p {}".format(self.ssh_port),
                    "-o StrictHostKeyChecking=no",
                    "-o ConnectTimeout=300",
                    "-o UserKnownHostsFile=/dev/null",
                    "-q",
                    "-i {}".format(self.__key_path),
                    "{}@{}".format(self.__user_name, self.private_ip),
                    "-x"]
        for port in local_pfwd:
            exec_cmd.insert(7, "-L {}:localhost:{}".format(port, port))
        for port in remote_pfwd:
            exec_cmd.insert(7, "-R {}:localhost:{}".format(port, port))

        cmd = exec_cmd + ["'"] + command + ["'"]
        self.master.run_on_master(cmd, local_pfwd, remote_pfwd, async)

    def run(self, command, local_pfwd = [], remote_pfwd = [], async = False):
    	if (master == ""):
    		# this is the master node
    		self.run_on_master(command, local_pfwd, remote_pfwd, async)
    	else:
    		# this is one of the worker nodes
    		self.run_on_worker(command, local_pfwd, remote_pfwd, async)

    def copy_to_master(self, src, dest):
        cprint("["+self.hostname+"]: copy file to master: "+src+" --> "+dest+".", self.__output_color)
        cmd = ["scp",
               "-i {}".format(self.__key_path),
               "-o StrictHostKeyChecking=no",
               "-o ConnectTimeout=300",
               "-o UserKnownHostsFile=/dev/null",
               "{}".format(src_path),
               "{}@{}:{}".format(self.__user_name, self.master_public_ip, dist_path)]
        subprocess.call(cmd)

    def copy_to_worker(self, src, dest, worker):
    	cprint("["+self.hostname+"]: copy file to worker: "+ src +" --> "+dest +".", self.__output_color)
    	cmd = ["scp",
               "-i {}".format(self.__remote_key_path),
               "-o StrictHostKeyChecking=no",
               "-o ConnectTimeout=300",
               "-o UserKnownHostsFile=/dev/null",
               "{}".format(src_path),
               "{}@{}:{}".format(self.__user_name, worker.private_ip, dist_path)]
        self.run_on_master(cmd)


    def get_ip(self):
        return self.private_ip    

    def get_hostname(self):
        return self.hostname

    
    def set_hostname(self):
        cprint("["+self.hostname+"]: set hostname.", self.__output_color)
        cmd = ["sudo hostname", self.hostname]
        self.run(cmd)

    def add_host_list(self, private_ip, hostname):
        cprint("["+self.hostname+"]: set hosts file for MPI.", self.__output_color)
        cmd = ["sudo echo",
               "\"{} {}\"".format(private_ip, hostname),
               "|",
               "tee --append",
               " /etc/hosts"]
        self.run(cmd)